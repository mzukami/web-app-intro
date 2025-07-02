def ask_lunch():
    lunch = input("今日の昼ごはんは何ですか? ")
    if lunch == "食べてない":
        print("忙しいね")
    else:
        print("いいね！{lunch}")

if __name__ == "__main__":
    ask_lunch()