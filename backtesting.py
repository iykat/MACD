import datetime as dt
from sqlite3 import Date
import yfinance as yf
from pandas_datareader import data as pdr
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np


class BackTest:
    def __init__(self, stock, startDate, endDate):
        yf.pdr_override()
        self.stock = stock
        self.startDate = startDate
        self.endDate = endDate
        
        self.df = pdr.get_data_yahoo(stock, self.startDate, self.endDate)
        
        self.df['EMA_12'] = self.df.iloc[:,4].ewm(span=12,  adjust=False).mean()
        self.df['EMA_26'] = self.df.iloc[:,4].ewm(span=26, adjust=False).mean()
        self.df['MACD'] = self.df.iloc[:,6] - self.df.iloc[:,7]
        self.df['SIGNAL'] = self.df.iloc[:,8].ewm(span=9, adjust=False).mean()
        self.df['DIFFSM'] = self.df.iloc[:,8] - self.df.iloc[:,9] 
        
        self.BuyDate = []
        self.BuyPrice = []
        self.SellDate = []
        self.SellPrice = []
        self.tradeRes = []
        

        
    def buyStock(self, date, price):
        self.BuyDate.append(date)
        self.BuyPrice.append(price)
        
    def sellStock(self, date, price, buyCost):
        gain = 100 * (price - buyCost)/buyCost
        self.SellDate.append(date)
        self.SellPrice.append(price)
        self.tradeRes.append(gain)
        
    def runAlgorithm(self):
        holding = False
        loc = 0
        buyingCost = -1
        lendf = self.df["MACD"].count()
        
        
        for i in self.df.index:
            close = self.df["Close"][i]
            currMacd = self.df["MACD"][i]
            currSignal = self.df["SIGNAL"][i]
            
            if (currMacd > currSignal):
                if not holding:
                    holding = True
                    buyingCost = close
                    self.buyStock(i, close)
            elif (currMacd < currSignal):
                if holding:
                    holding = False
                    self.sellStock(i, close, buyingCost)
                    
            if (loc == lendf - 1 and holding):
                holding = False
                self.sellStock(i, close, buyingCost)
                
            loc += 1
            
        self.df.insert(11, "Date", self.df.index, False)
        
    def getResults(self):
        tradesWon = 0
        numTrades = len(self.tradeRes)
        
        for i in range(numTrades):
            if (self.tradeRes[i] > 0):
                tradesWon += 1
        winRate = (tradesWon / numTrades) * 100
        
        maxReturn = self.tradeRes[0]
        maxDate = str(self.SellDate[0])
        avgReturn = sum(self.tradeRes)/numTrades 
        
        for i in range(1, numTrades):
            if (self.tradeRes[i] > maxReturn):
                maxDate = str(self.SellDate[i])
                maxReturn = self.tradeRes[i]
                
        print("Results for trading " + self.stock + " from " + str(self.startDate) + " to " + str(self.endDate) + ":")
        print("Max Return on " + maxDate + " earning a gain of " + str(round(maxReturn,2)) + "%.")
        print("This strategy has a winrate of "+ str(round(winRate,2)) + "% by placing " + str(numTrades) + " trades and earned an average return of " + str(round(avgReturn,2)) + "%.")
        
    def createTradingView(self):
        candlestickFig = go.Figure(data=[go.Candlestick(x=self.df['Date'],
                open=self.df['Open'],
                high=self.df['High'],
                low=self.df['Low'],
                close=self.df['Close'])])
        EMA_12Fig = px.line(self.df, x='Date', y="EMA_12")
        EMA_12Fig.update_traces(line=dict(color = 'rgba(238,130,238,0.7)'))
        EMA_26Fig = px.line(self.df, x='Date', y="EMA_26")
        BuyFig = go.Figure(data=go.Scatter(x=self.BuyDate, y=self.BuyPrice, mode='markers'))
        BuyFig.update_traces(marker=dict(color = 'rgba(60, 179, 113,1)', size=9, line=dict(width=1,
                                                color='DarkSlateGrey')))
        SellFig = go.Figure(data=go.Scatter(x=self.SellDate, y=self.SellPrice, mode='markers'))
        SellFig.update_traces(marker=dict(color = 'rgba(255, 0, 0,1)', size=9, line=dict(width=1,
                                                color='DarkSlateGrey')))
        topFig = go.Figure(data=EMA_12Fig.data + EMA_26Fig.data + candlestickFig.data + BuyFig.data + SellFig.data)
        topFig.update_layout(xaxis_rangeslider_visible=False)


        macdfig=px.line(self.df, x='Date', y="MACD")
        signalFig=px.line(self.df, x='Date', y="SIGNAL")
        signalFig.update_traces(line=dict(color = 'rgba(255,165,0,0.7)'))
        self.df["Color"]=np.where(self.df["DIFFSM"]<0, 'rgb(255, 0, 0)', 'rgb(60, 179, 113)')
        DiffFig = go.Figure()
        DiffFig.add_trace(
            go.Bar(x=self.df['Date'],
                y=self.df['DIFFSM'],
                marker_color=self.df['Color']))
        DiffFig.update_layout(barmode='stack')
        botFig=go.Figure(data=macdfig.data + signalFig.data + DiffFig.data)

        combinedfig = make_subplots(rows=2, cols=1,
                            shared_xaxes=True,
                            vertical_spacing=0.02,
                            row_heights=[0.7,0.3],
                            shared_yaxes=False)

        #EMA_12Fig = px.l
        for i in range(len(topFig.data)):
            combinedfig.add_trace(topFig.data[i], row=1, col=1)
        for i in range(len(botFig.data)):
            combinedfig.add_trace(botFig.data[i], row=2, col=1)
        combinedfig.update_layout(xaxis_rangeslider_visible=False)
        combinedfig.update_xaxes(range=[self.startDate, self.endDate], row=2, col=1)
        combinedfig.show()
                
        
        
         
        
testObject = BackTest("TSLA", dt.datetime(2011,1,1), dt.datetime.now())
testObject.runAlgorithm()
testObject.getResults()
testObject.createTradingView() 
        
        
        