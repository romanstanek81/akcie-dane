import sys
import csv
import copy

if len(sys.argv) < 2:
    print ("No csv file given as argument.")
    exit(0)

csv_file = sys.argv[1]


class Transaction:
    def __init__(self, csv_line) -> None:
        self._csv_line = csv_line
        pass

    def is_valid(self):
        if len(self._csv_line) < 6:
            return False
        return self.is_buy() or self.is_sell()
    
    def is_buy(self):
        return self._csv_line[1] == 'Nákup'
    
    def is_sell(self):
        return self._csv_line[1] == 'Prodej'
    
    def get_date(self):
        return self._csv_line[0]
    
    def get_year(self):
        return int(self._csv_line[0][-4:])
    
    def get_amount(self):
        return float(self._csv_line[2])

    def get_price(self):
        return float(self._csv_line[3])

    def get_volume(self):
        return float(self._csv_line[4])

    def get_fee(self):
        return float(self._csv_line[5])

    def get_fee_by_amount(self, amount):
        return (float(self.get_amount() - amount) / float(self.get_amount())) * self.get_fee() # percentual

    def get_tran_by_amount(self, amount):
        if self.get_amount() == amount:
            return None
        final_amount = self.get_amount() - amount
        final_fee = self.get_fee() - self.get_fee_by_amount(amount)
        final_volume = self.get_volume() - amount * self.get_price()
        t = Transaction([self._csv_line[0], self._csv_line[1], final_amount, self._csv_line[3], final_volume, final_fee])
        return t

    def __str__(self) -> str:
        return ",".join([str(x) for x in self._csv_line])

class Transactions:
    def __init__(self, csv_file) -> None:
        self._trans = []
        self._ptr = 0
        if csv_file != "":
            self.load_from_csv_file(csv_file)
    
    def reset_ptr(self):
        self._ptr = 0

    def get_next(self):
        t = None
        if self._ptr < len(self._trans):
            t = self._trans[self._ptr]
            self._ptr = self._ptr + 1
        return t
    
    def _convert(self, csv_line):
        if len(csv_line) < 6:
            return
        for i in range(2,len(csv_line)):
            if isinstance(csv_line[i], str):
                csv_line[i] = csv_line[i].replace(",", ".")
        if csv_line[1] == 'Prodej':
            # remove the '-' from amount and volume
            csv_line[2] = csv_line[2][1:]
        elif csv_line[1] == 'Nákup':
            csv_line[4] = csv_line[4][1:]    
    
    def load_from_csv_file(self, csv_file):
        with open(csv_file, 'rt') as f:
            csv_reader = csv.reader(f,delimiter =';')
            first = True
            for line in csv_reader:
                if first:
                    first = False
                    continue
                self._convert(line)
                t = Transaction(line)
                if t.is_valid():
                    self._trans.append(t)


class Selling:
    def __init__(self, trans) -> None:
        self._trans = copy.deepcopy(trans)
        pass

    def get_sell_next_year(self):
        sell_volume = 0.0
        sell_fee = 0.0
        sell_amount = 0
        year = 0
        while True:
            t = self._trans.get_next()
            if not t:
                break
            if t.is_sell():
                if year == 0:
                    year = t.get_year()
                else:
                    if year != t.get_year(): # sell from another year.
                        break
                sell_volume = sell_volume + t.get_volume()
                sell_fee = sell_fee + t.get_fee()
                sell_amount = sell_amount + t.get_amount()
                #print ("S {} sell_volume: {}, sell_fee:{} ,sell_amount: {}".format(t.get_date(), sell_volume, sell_fee, sell_amount))

        return sell_volume, sell_fee, sell_amount, year
    

class Buying:
    def __init__(self, trans) -> None:
        self._trans = copy.deepcopy(trans)
        self._trans.reset_ptr()
        self._last_tran_leftover = None

    def get_buy_by_amount(self, amount):
        buy_volume = 0.0
        buy_fee = 0.0
        buy_amount = 0
        while True:
            if self._last_tran_leftover:
                t = self._last_tran_leftover
                self._last_tran_leftover = None
            else:
                t = self._trans.get_next()
                if not t:
                    break
                if not t.is_buy():
                    continue

            if buy_amount + t.get_amount() > amount:
                amount_to_buy = amount - buy_amount
                buy_amount = buy_amount + amount_to_buy
                buy_volume = buy_volume + amount_to_buy * t.get_price()
                buy_fee = buy_fee + t.get_fee_by_amount(amount_to_buy)
                self._last_tran_leftover = t.get_tran_by_amount(amount_to_buy)
                #print("bx: {}".format(self._last_tran_leftover))
                #print ("Bx {} buy_volume: {}, buy_fee:{} ,buy_amount: {}".format(t.get_date(), buy_volume, buy_fee, buy_amount))
                break
            else:
                buy_volume = buy_volume + t.get_volume()
                buy_fee = buy_fee + t.get_fee()
                buy_amount = buy_amount + t.get_amount()
                #print ("B {} buy_volume: {}, buy_fee:{} ,buy_amount: {}".format(t.get_date(), buy_volume, buy_fee, buy_amount))
                if buy_amount == amount:
                    break

        return buy_volume, buy_fee


class Taxes:
    def __init__(self, trans) -> None:
        self._selling = Selling(trans)
        self._buying = Buying(trans)
        pass

    def process(self):
        while True:
            sell_volume, sell_fee, sell_amount, year = self._selling.get_sell_next_year()
            if not year:
                break
            buy_volume, buy_fee = self._buying.get_buy_by_amount(sell_amount)
            print ("YEAR: " + str(year))
            print ("vars: sell_volume {}, sell_fee {}, sell_amount {}, buy_volume {}, buy_fee {}".format(sell_volume, sell_fee, sell_amount,buy_volume, buy_fee))
            print ("result: {}".format(sell_volume - buy_volume - buy_fee - sell_fee))



trans = Transactions(csv_file)
taxes = Taxes(trans)
taxes.process()
