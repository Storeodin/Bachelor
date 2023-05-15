import urllib2
import json
import datetime
import time

class GetData:
    def __init__(self):
        self.dateToday = datetime.datetime.now().strftime("%Y/%m-%d")
        self.dateTomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y/%m-%d")
        self.url = "https://www.hvakosterstrommen.no/api/v1/prices/"
        self.priceToday = []
        self.priceTomorrow = []
        self.timeToday = []
        self.timeTomorrow = []

    def RetrievePricesToday(self):
        responseToday = urllib2.urlopen(self.url + self.dateToday + "_NO1.json").read()
        responseInfoToday = json.loads(responseToday)

        i = 0
        for row in responseInfoToday:
            self.priceToday.append(row["NOK_per_kWh"])
            self.timeToday.append(i)
            i += 1

    def RetrievePricesTomorrow(self):
        while True:
            try:
                responseTomorrow = urllib2.urlopen(self.url + self.dateTomorrow + "_NO1.json").read()
                responseInfoTomorrow = json.loads(responseTomorrow)
                break
            except:
                print("Tomorrow prices have not been updated yet")
                print("Today's prices: ", self.priceToday)
                time.sleep(3600)  # sleep for 1 hour

        i = 0
        for row in responseInfoTomorrow:
            self.priceTomorrow.append(row["NOK_per_kWh"])
            self.timeTomorrow.append(i)
            i += 1

class Data:
    def __init__(self):
        self.priceToday = []
        self.priceTomorrow = []

    def GetData(self, gd):
        self.priceToday = gd.priceToday
        self.priceTomorrow = gd.priceTomorrow

# Initialize classes
gd = GetData()
data = Data()

# Retrieve prices
gd.RetrievePricesToday()
gd.RetrievePricesTomorrow()

# Get data
data.GetData(gd)

# Create dataset
dataset = DefaultCategoryDataset()
for i in range(len(gd.timeToday)):
    dataset.addValue(gd.priceToday[i], 'I dag', Integer(i))
for i in range(len(gd.timeTomorrow)):
    dataset.addValue(gd.priceTomorrow[i], 'I morgen', Integer(i))

# Create chart
chart = ChartFactory.createBarChart(
    'Strompriser',
    'Tid [Timer]',
    'Pris [NOK]',
    dataset,
    PlotOrientation.VERTICAL,
    True,
    True,
    False
)


# Create frame
frame = JFrame('Strompriser')
frame.setSize(Dimension(640, 480))
frame.contentPane.add(chart_panel)
frame.visible = True

print("Today's prices: ",priceToday)
print("Tomorrow's prices: ",priceTomorrow)