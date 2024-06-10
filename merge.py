import pandas as pd

df1 = pd.read_table('train_ENG.txt')
print(df1.head())

df2 = pd.read_table('train_HIN.txt')
print(df2.head())

print(df1.shape)
print(df2.shape)