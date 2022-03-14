import os
from datetime import date
import tkinter as tk
from tkinter import *
from tkinter import ttk
import mplfinance as mpl
from matplotlib.backends._backend_tk import NavigationToolbar2Tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from functions import *
import pickle


class MainWindow:
    def load_session(self):
        if os.path.exists("session.pkl"):
            with open("session.pkl", "rb") as pickle_in:
                self.session_info = pickle.load(pickle_in)

            if len(self.session_info) > 0:
                self.account = self.session_info[0]
                self.label_account["text"] += self.session_info[0]
                self.balance = self.session_info[1]
                balance = ("%.2f" % self.balance)
                self.label_balance["text"] += str(balance)
                self.order_id = self.session_info[2]

                for i in range(3, len(self.session_info)):
                    order = self.session_info[i]
                    # 0"order_id", 1"symbol", 2"time", 3"type", 4"size", 5"open_price", 6"current_price", 7"profit"
                    self.orders_table.insert(parent="", index="end", text="",
                                             values=(order[0], order[1], order[2], order[3],
                                                     order[4], order[5], order[6], order[7]))
        else:
            self.session_info.append(self.account)
            self.session_info.append(self.balance)
            self.session_info.append(self.order_id)

            self.label_account["text"] += self.account
            balance = ("%.2f" % self.balance)
            self.label_balance["text"] += str(balance)

    def __init__(self, master):
        self.master = master
        self.frame = tk.Frame(self.master)
        self.session_info = []

        self.forex_table()
        self.create_buttons_frame()
        self.create_account_frame()
        self.create_orders_table()
        self.draw_chart()

        self.account = "Tester"
        self.balance = 100000
        self.order_id = 1000

        self.load_session()

    # mode="add" use when adding new order order must be given
    # mode="remove" use when closing order order_id must be given
    # mode="update" use when refreshing order and order_id must be given
    def save_session(self, order=[], order_id="", mode="add"):
        if mode == "add":
            self.session_info[0] = self.account
            self.session_info[1] = self.balance
            self.session_info[2] = self.order_id
            self.session_info.append(order)
            with open("session.pkl", "wb") as pickle_out:
                pickle.dump(self.session_info, pickle_out)

        elif mode == "remove":
            self.session_info[0] = self.account
            self.session_info[1] = self.balance
            self.session_info[2] = self.order_id

            for i in range(3, len(self.session_info)):
                if self.session_info[i][0] == order_id:
                    self.session_info.pop(i)
                    break

            with open("session.pkl", "wb") as pickle_out:
                pickle.dump(self.session_info, pickle_out)

        elif mode == "update":
            self.session_info[0] = self.account
            self.session_info[1] = self.balance
            self.session_info[2] = self.order_id

            for i in range(3, len(self.session_info)):
                if self.session_info[i][0] == order_id:
                    self.session_info[i][6] = order[6]
                    self.session_info[i][7] = order[7]
                    break

            with open("session.pkl", "wb") as pickle_out:
                pickle.dump(self.session_info, pickle_out)



    def buy_event(self):
        selected_index = self.table.focus()
        self.refresh_event()
        item = self.table.item(selected_index)
        ask_price = float(item["values"][2])
        lot_size = self.lot_size.get()

        if lot_size * ask_price > self.balance:
            return

        self.balance -= lot_size * ask_price
        balance = ("%.2f" % self.balance)
        self.label_balance["text"] = f"Balance ($): {balance}"

        profit = float(item["values"][1]) * lot_size - ask_price * lot_size

        # 0"order_id", 1"symbol", 2"time", 3"type", 4"size", 5"open_price", 6"current_price", 7"profit"
        order = [self.order_id, item["values"][0], date.today(), "buy", lot_size, ask_price, item["values"][1], profit]
        self.order_id += 1
        self.save_session(order)

        self.orders_table.insert(parent="", index="end", text="",
                                 values=(order[0],
                                         order[1],
                                         order[2],
                                         order[3],
                                         order[4],
                                         order[5],
                                         order[6],
                                         ("%.2f" % order[7])
                                         ))

    def close_event(self):
        self.refresh_event()
        selected_index = self.orders_table.focus()
        item = self.orders_table.item(selected_index)
        order_id = item["values"][0]
        bid_price = float(item["values"][6])
        size = item["values"][4]

        self.balance += bid_price * float(size)
        balance = ("%.2f" % self.balance)
        self.label_balance["text"] = f"Balance ($): {balance}"
        self.save_session(order_id=order_id, mode="remove")

        self.orders_table.delete(selected_index)
        self.button_close["state"] = "disabled"

    def refresh_event(self):
        for i in self.table.get_children():
            self.table.delete(i)
        self.table.update()

        live_df = get_live_dataframe()
        for i in range(len(live_df)):
            self.table.insert(parent="", index="end", iid=str(i), text="",
                              values=(live_df["symbol"][i], live_df["bid"][i], live_df["ask"][i]))

        self.table.selection_set(0)
        item = self.table.selection()
        self.table.focus(item)

        self.refresh_orders(live_df)

    def get_bid_by_symbol(self, df, symbol):
        for i in range(len(df)):
            if df["symbol"][i] == symbol:
                return df["bid"][i]
        return -1

    def refresh_orders(self, df):
        for i in self.orders_table.get_children():
            item = self.orders_table.item(i)
            symbol = item["values"][1]
            new_bid = self.get_bid_by_symbol(df, symbol)

            if new_bid == -1:
                new_bid = item["values"][6]

            profit = float(new_bid) * float(item["values"][4]) - float(item["values"][5]) * float(item["values"][4])

            # 0"order_id", 1"symbol", 2"time", 3"type", 4"size", 5"open_price", 6"current_price", 7"profit"
            self.orders_table.item(i, values=(item["values"][0],
                                              item["values"][1],
                                              item["values"][2],
                                              item["values"][3],
                                              item["values"][4],
                                              item["values"][5],
                                              new_bid,
                                              ("%.2f" % profit)))

            self.orders_table.update()
            self.save_session(self.orders_table.item(i)["values"], item["values"][0], mode="update")

    def create_buttons_frame(self):
        buttons_frame = Frame(master=self.frame)
        buttons_frame.grid(row=1, column=0)

        self.label_selected_pair = Label(buttons_frame, text="Selected pair: ")
        self.label_selected_pair.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        label_lot_size = Label(buttons_frame, text="Lot size")
        label_lot_size.grid(row=1, column=0, columnspan=2)

        self.lot_size = DoubleVar(value=100)

        Radiobutton(buttons_frame, text="100", variable=self.lot_size, value=100).grid(row=2, column=0)
        Radiobutton(buttons_frame, text="1000", variable=self.lot_size, value=1000).grid(row=2, column=1)
        Radiobutton(buttons_frame, text="10000", variable=self.lot_size, value=10000).grid(row=3, column=0, pady=(0, 20))
        Radiobutton(buttons_frame, text="100000", variable=self.lot_size, value=100000).grid(row=3, column=1, pady=(0, 20))

        self.button_buy = Button(buttons_frame, text="Buy", width=15, command=self.buy_event, background="green")
        self.button_sell = Button(buttons_frame, text="Sell", width=15, state=DISABLED, background="grey")
        self.button_refresh = Button(buttons_frame, text="Refresh", width=15, command=self.refresh_event)
        self.button_close = Button(buttons_frame, text="Close", width=15, command=self.close_event, state=DISABLED)
        self.button_buy.grid(row=4, column=0, padx=(0, 10))
        self.button_sell.grid(row=4, column=1, padx=(10, 0))
        self.button_refresh.grid(row=5, column=0, padx=(0, 10), pady=(25, 0))
        self.button_close.grid(row=5, column=1, padx=(10, 0), pady=(25, 0))

    def create_account_frame(self):
        account_frame = Frame(master=self.frame)
        account_frame.grid(row=2, column=0)

        self.label_account = Label(account_frame, text="Account: ")
        self.label_balance = Label(account_frame, text="Balance ($): ")

        self.label_account.grid(row=0, column=0)
        self.label_balance.grid(row=1, column=0)

    def get_symbol(self):
        try:
            selected_index = self.table.focus()
            item = self.table.item(selected_index)
            symbol = item["values"][0]
        except IndexError:
            symbol = "USDCAD"

        return symbol

    def draw_chart(self, event=""):
        symbol = self.get_symbol()
        self.label_selected_pair["text"] = f"Selected pair: {symbol}"

        df = get_history_dataframe(symbol)
        df.date = pd.to_datetime(df.date)
        df = df.set_index("date")

        chart_frame = Frame(master=self.frame)
        chart_frame.grid(row=0, column=1, rowspan=3)

        fig, ax = mpl.plot(df, type='candle', style="yahoo", title=symbol, returnfig=True)

        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.draw()
        canvas.get_tk_widget().grid(row=0, column=0)

        toolbar_frame = Frame(master=self.frame)
        toolbar_frame.grid(row=3, column=1)
        toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
        toolbar.update()

    def forex_table(self):
        forex_frame = Frame(master=self.frame)
        forex_frame.grid(row=0, column=0, sticky=N)

        scrollbar = Scrollbar(forex_frame)

        self.table = ttk.Treeview(forex_frame, yscrollcommand=scrollbar.set, selectmode="browse")
        scrollbar.config(command=self.table.yview)

        self.table.grid(row=0, column=0)
        scrollbar.grid(row=0, column=1, sticky=NS)

        self.table.bind("<<TreeviewSelect>>", self.draw_chart)

        # define our column

        self.table["columns"] = ("symbol", "bid", "ask")

        # format columns
        self.table.column("#0", width=0, stretch=NO)
        self.table.column("symbol", anchor=CENTER, width=80)
        self.table.column("bid", anchor=CENTER, width=80)
        self.table.column("ask", anchor=CENTER, width=80)

        # create headings
        self.table.heading("#0", text="", anchor=CENTER)
        self.table.heading("symbol", text="Symbol", anchor=CENTER)
        self.table.heading("bid", text="Bid", anchor=CENTER)
        self.table.heading("ask", text="Ask", anchor=CENTER)

        live_df = get_live_dataframe()
        for i in range(len(live_df)):
            self.table.insert(parent="", index="end", iid=str(i), text="",
                              values=(live_df["symbol"][i], live_df["bid"][i], live_df["ask"][i]))

        self.table.selection_set(0)
        item = self.table.selection()
        self.table.focus(item)

    def enable_close(self, event=""):
        self.button_close["state"] = "normal"

    def create_orders_table(self):
        scrollbar2 = Scrollbar(self.frame)
        self.orders_table = ttk.Treeview(self.frame, yscrollcommand=scrollbar2.set, selectmode="browse")
        scrollbar2.config(command=self.table.yview)

        self.orders_table.grid(row=4, column=0, columnspan=3, sticky=EW)
        scrollbar2.grid(row=4, column=3, sticky=NS)

        self.orders_table.bind("<<TreeviewSelect>>", self.enable_close)

        self.orders_table["columns"] = ("id", "symbol", "time", "type", "size", "open_price", "current_price", "profit")

        # formatting
        self.orders_table.column("#0", width=0, stretch=NO)
        self.orders_table.column("id", anchor=CENTER, width=80)
        self.orders_table.column("symbol", anchor=CENTER, width=80)
        self.orders_table.column("time", anchor=CENTER, width=80)
        self.orders_table.column("type", anchor=CENTER, width=80)
        self.orders_table.column("size", anchor=CENTER, width=80)
        self.orders_table.column("open_price", anchor=CENTER, width=80)
        self.orders_table.column("current_price", anchor=CENTER, width=80)
        self.orders_table.column("profit", anchor=CENTER, width=80)

        # headings
        self.orders_table.heading("#0", text="", anchor=CENTER)
        self.orders_table.heading("id", text="Order ID", anchor=CENTER)
        self.orders_table.heading("symbol", text="Symbol", anchor=CENTER)
        self.orders_table.heading("time", text="Time", anchor=CENTER)
        self.orders_table.heading("type", text="Type", anchor=CENTER)
        self.orders_table.heading("size", text="Size", anchor=CENTER)
        self.orders_table.heading("open_price", text="Open price", anchor=CENTER)
        self.orders_table.heading("current_price", text="Current price", anchor=CENTER)
        self.orders_table.heading("profit", text="Profit", anchor=CENTER)

        self.frame.grid()


def main():
    root = tk.Tk()
    root.geometry("1100x860")
    root.iconbitmap("icon.ico")
    root.title("Forex trading")
    app = MainWindow(root)
    root.mainloop()


if __name__ == '__main__':
    main()
