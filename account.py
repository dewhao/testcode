import json
import datetime
import os


recs = []
bal = 0.0
bdg = 1000.0
data_file = "account_data.json"

# 计算收支列表总金额
def calc_total_amt(rec_list):
    total = 0
    for r in rec_list:
        total += r["amount"]
    return total

# 新增一条收支记录，更新余额，并检查月度预算
def add_record(date_str, type_str, amt, category, remark):
    global bal, recs
    if amt > 0:
        try:
            datetime.datetime.strptime(date_str, "%Y-%m-%d")
            valid_cats = ["餐饮", "交通", "购物", "工资", "奖金", "其他"]
            if category in valid_cats:
                if type_str in ["income", "expense"]:
                    if len(recs) == 0:
                        new_id = 1
                    else:
                        new_id = max(r["id"] for r in recs) + 1
                    if type_str == "income":
                        bal += amt
                    else:
                        bal -= amt
                        month = date_str[:7]
                        month_exp = sum(r["amount"] for r in recs if r["type"] == "expense" and r["date"].startswith(month))
                        if month_exp + amt > bdg:
                            print("警告：本月支出已超预算！")
                        elif month_exp + amt > bdg * 0.8:
                            print("提醒：本月支出已达预算80%")
                    rec = {
                        "id": new_id,
                        "date": date_str,
                        "type": type_str,
                        "amount": amt,
                        "category": category,
                        "remark": remark
                    }
                    recs.append(rec)
                    save_data()
                    print(f"记录添加成功，ID：{new_id}")
                else:
                    print("错误：类型只能是income或expense")
            else:
                print("错误：分类不合法")
        except ValueError:
            print("错误：日期格式错误，应为YYYY-MM-DD")
    else:
        print("错误：金额必须大于0")


# 修改单条收支记录，自动重新计算结余并触发预算校验与预警
def update_record(rec_id, date_str, type_str, amt, category, remark):
    global bal, recs
    if amt > 0:
        try:
            datetime.datetime.strptime(date_str, "%Y-%m-%d")
            valid_cats = ["餐饮", "交通", "购物", "工资", "奖金", "其他"]
            if category in valid_cats:
                if type_str in ["income", "expense"]:
                    target = None
                    for r in recs:
                        if r["id"] == rec_id:
                            target = r
                            break
                    if target:
                        if target["type"] == "income":
                            bal -= target["amount"]
                        else:
                            bal += target["amount"]
                        if type_str == "income":
                            bal += amt
                        else:
                            bal -= amt
                        target["date"] = date_str
                        target["type"] = type_str
                        target["amount"] = amt
                        target["category"] = category
                        target["remark"] = remark
                        save_data()
                        print(f"记录ID {rec_id} 更新成功")
                    else:
                        print("错误：记录不存在")
                else:
                    print("错误：类型只能是income或expense")
            else:
                print("错误：分类不合法")
        except ValueError:
            print("错误：日期格式错误，应为YYYY-MM-DD")
    else:
        print("错误：金额必须大于0")

# 删除单条收支记录，并自动更新结余
def delete_record(rec_id):
    global recs, bal
    if len(recs) == 0:
        print("错误：暂无记录")
        return
    target = None
    for r in recs:
        if r["id"] == rec_id:
            target = r
            break
    if target:
        if target["type"] == "income":
            bal -= target["amount"]
        else:
            bal += target["amount"]
        recs.remove(target)
        save_data()
        print(f"记录ID {rec_id} 删除成功")
    else:
        print("错误：记录不存在")


# 按日期范围查询收支记录
def query_by_date(start_date, end_date):
    res = []
    for r in recs:
        if r["date"] >= start_date and r["date"] <= end_date:
            res.append(r)
    if len(res) == 0:
        print("未找到符合条件的记录")
    else:
        for r in res:
            print(r)
    return res

# 按类型查询收支记录
def query_by_type(type_str):
    res = []
    for r in recs:
        if r["type"] == type_str:
            res.append(r)
    if len(res) == 0:
        print("未找到符合条件的记录")
    else:
        for r in res:
            print(r)
    return res

# 按分类查询收支记录
def query_by_category(category):
    res = []
    for r in recs:
        if r["category"] == category:
            res.append(r)
    if len(res) == 0:
        print("未找到符合条件的记录")
    else:
        for r in res:
            print(r)
    return res

# 获取月度统计信息
def get_monthly_stats(month_str):
    if len(recs) == 0:
        print("暂无记录")
        return
    income_total = 0.0
    expense_total = 0.0
    cat_stats = {}
    for r in recs:
        if r["date"].startswith(month_str):
            if r["type"] == "income":
                income_total += r["amount"]
            else:
                expense_total += r["amount"]
                if r["category"] in cat_stats:
                    cat_stats[r["category"]] += r["amount"]
                else:
                    cat_stats[r["category"]] = r["amount"]
    net = income_total - expense_total
    print(f"===== {month_str} 月度统计 =====")
    print(f"总收入：{income_total:.2f} 元")
    print(f"总支出：{expense_total:.2f} 元")
    print(f"净结余：{net:.2f} 元")
    print(f"当前预算：{bdg:.2f} 元")
    if expense_total > bdg:
        print("状态：超预算")
    else:
        print("状态：预算内")
    print("支出分类占比：")
    for cat, amt in cat_stats.items():
        ratio = amt / expense_total * 100
        print(f"  {cat}: {amt:.2f} 元 ({ratio:.1f}%)")
    return income_total, expense_total, net

# 设置月度预算
def set_budget(new_bdg):
    global bdg
    if new_bdg > 0:
        bdg = new_bdg
        print(f"预算已设置为：{bdg:.2f} 元")
    else:
        print("错误：预算必须大于0")

# 保存数据
def save_data():
    data = {
        "records": recs,
        "balance": bal,
        "budget": bdg
    }
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 加载数据
def load_data():
    global recs, bal, bdg
    if os.path.exists(data_file):
        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            recs = data.get("records", [])
            bal = data.get("balance", 0.0)
            bdg = data.get("budget", 1000.0)
    else:
        recs = []
        bal = 0.0
        bdg = 1000.0


def main():
    load_data()
    print("=== 简易记账系统 ===")
    while True:
        print("\n菜单：")
        print("1. 新增记录")
        print("2. 删除记录")
        print("3. 修改记录")
        print("4. 按日期查询")
        print("5. 按类型查询")
        print("6. 按分类查询")
        print("7. 月度统计")
        print("8. 设置预算")
        print("9. 查看当前结余")
        print("0. 退出")
        choice = input("请输入选项：")
        if choice == "1":
            date = input("请输入日期(YYYY-MM-DD)：")
            type_str = input("请输入类型(income/expense)：")
            amt = float(input("请输入金额："))
            category = input("请输入分类：")
            remark = input("请输入备注：")
            add_record(date, type_str, amt, category, remark)
        elif choice == "2":
            rec_id = int(input("请输入要删除的记录ID："))
            delete_record(rec_id)
        elif choice == "3":
            rec_id = int(input("请输入要修改的记录ID："))
            date = input("请输入日期(YYYY-MM-DD)：")
            type_str = input("请输入类型(income/expense)：")
            amt = float(input("请输入金额："))
            category = input("请输入分类：")
            remark = input("请输入备注：")
            update_record(rec_id, date, type_str, amt, category, remark)
        elif choice == "4":
            start = input("请输入开始日期：")
            end = input("请输入结束日期：")
            query_by_date(start, end)
        elif choice == "5":
            t = input("请输入类型(income/expense)：")
            query_by_type(t)
        elif choice == "6":
            c = input("请输入分类：")
            query_by_category(c)
        elif choice == "7":
            month = input("请输入月份(YYYY-MM)：")
            get_monthly_stats(month)
        elif choice == "8":
            b = float(input("请输入新预算："))
            set_budget(b)
        elif choice == "9":
            print(f"当前结余：{bal:.2f} 元")
        elif choice == "0":
            save_data()
            print("已保存数据，退出系统")
            break
        else:
            print("无效选项，请重新输入")


if __name__ == "__main__":
    main()
