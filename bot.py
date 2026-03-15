
while True:
    try:
        print("Scanner attivo")
        send("scanner attivo")
        time.sleep(30)

    except Exception as e:
        print(e)
        time.sleep(30)
