# Ruslan G.
# Демонстрация работы скрипта https://youtu.be/pwwpx4YFFec
# Согласно условиям задачи, Компания получает платежи за приложение по системе ежемесячной подписки. 
# Минимальный платеж - 500 руб. Доступны также дополнительные услуги.
# Компания проводила маркетинговую кампанию в 2019 - 2020 гг.
# Цель - визуализировать результаты когортного анализа среднего платежа за приложение (ARPU), числа активных пользователей 
# и числа пользователей, переставших оплачивать подписку за приложение, с аналитикой по группам в зависимости от месяца привлечения.

import pandas as pd
import datetime
import seaborn as sns
import matplotlib.pyplot as plt
!pip install easygui #установка библиотеки easygui, необходимой для открытия окна выбора файла
import easygui

# выбрать нужный файл в окне интерфейса
file_path = easygui.fileopenbox()


# Программа читает файл с расширением xlsx, содержащий информацию о платежах за приложение. 
# Файл имеет следующие столбцы Date (дата осуществления платежа), Amount (сумма оплаты в рублях), User (уникальный код пользователя).
income = pd.read_excel(file_path)

# находим уникальные значения контрагентов и формируем их список
# формируем саппорт-таблицу с названиями контрагентов "User" и столбцом их привлечения "In date"
uclist = pd.DataFrame({'User': income['User'].unique()}, columns=["User", "In date"])

# заполняем саппорт-таблицу
for i in range(len(uclist)):
    for j in range(len(income["Date"])):
        if uclist['User'].iloc[i] == income["User"].iloc[j]:
            uclist['In date'].iloc[i] = income["Date"].iloc[j].strftime("%B %Y")
            break


# узнаем максимальный и минимальный месяцы в столбце date в income
tmax = income["Date"].max()
tmin = income["Date"].min()


# рассчитываем период активности в месяцах из Income
mnumb = tmax.month - tmin.month + 12 * (tmax.year - tmin.year) # число месяцев активности

# формируем таблицу для последующего заполнения размера (mnumb + 1 на mnumb + 2). 1-й столбец используется для указания даты привлечения
panel = pd.DataFrame(0, index = range(mnumb + 1), columns = ["Month & Year"] + [i for i in range(0, mnumb + 1)])


mm = tmin.month # первый месяц в периоде
yy = tmin.year # первый год в периоде

# Заполняем столбец "Month & Year" в таблице. В последствии столбец будет использоваться для заполнения числовой информации в таблице.
# Цикл for для последовательного заполнения столбца "Month & Year"
for i in range(mnumb + 1):
    panel["Month & Year"].iloc[i] = datetime.date(yy, mm, 1).strftime("%B %Y")
    if mm == 12:
        yy += 1
        mm = 1
    else:
        mm += 1

# создаем таблицы для доходов пользователей (panelIncome), количества активных пользователей и расчета коэффициента оттока (panelChurn)
panelArpu = panel.copy(deep = True)
panelActiveUs = panel.copy(deep = True)
panelChurn = panel.copy(deep = True)

# заменяем нулевые значения на единичные для последующего использования mask при формировании heatmap
panelChurn = panelChurn.replace([0], 1)

# дополняем таблицу income данными о дате первой покупки каждого из пользователей
income = income.merge(uclist, left_on = 'User', right_on = 'User', how = 'left')


def timeshift(date0: str, shift: int):
    """
    Функция рассчитывает сдвиг по количеству месяцев (shift) относительно даты (date0) в формате '%B %Y'.
    На выходе выдает дату с учетом сдвига в формате '%B %Y'.
    """
    m1 = datetime.datetime.strptime(date0, '%B %Y').month
    y1 = datetime.datetime.strptime(date0, '%B %Y').year
    mnew = shift % 12 + m1
    if mnew > 12:
        mnew %= 12
        y1 += 1
    ynew = shift // 12 + y1
    return datetime.date(ynew, mnew, 1).strftime("%B %Y")

# заполняем таблицы данными из Income
for i in range(mnumb + 1):  # month year - ряды
    k = 0
    for j in range(mnumb + 1):  # столбцы 0 - (mnumb + 1)
        if k < mnumb + 1 - i:
            incsum = 0
            uparts = []
            for l in range(len(income["Date"])): #income rows
                if (income["In date"][l] == panel["Month & Year"][i] 
                and 
                income["Date"][l].strftime("%B %Y") == timeshift(income["In date"][l], j)):
                    incsum += income["Amount"][l]  # заполнение суммы среднего дохода с одного пользователя когорты в месяц
                    uparts.append(income['User'][l])  # количество активных пользователей
            k += 1  # счетчик для отсечения данных вне периода
            upnumber = len(list(set(uparts)))
            panelArpu[j][i] = incsum/upnumber/100
            panelArpu
            panelActiveUs[j][i] = int(upnumber)
            if j > 0:
                panelChurn[j][i] = upnumber - panelActiveUs[j - 1][i] #заполнение колонка 1 и т.д., churn
            else:
                panelChurn[j][i] = 0 #заполнение начального столбца нулями

#переназначаем 1й столбец в таблице как индекс
panelArpu = panelArpu.set_index('Month & Year')            
panelActiveUs = panelActiveUs.set_index('Month & Year')
panelChurn = panelChurn.set_index('Month & Year')

#формируем heatmap активных пользователей
plt.subplots(figsize=(14, 9))
sns.heatmap(panelActiveUs, annot = True, vmin = panelActiveUs[panelActiveUs > 0].min().min(), vmax = panelActiveUs.max().max(), mask = panelActiveUs < panelActiveUs[panelActiveUs > 0].min().min(), cmap = "cool")
plt.xlabel('Months after First Payment', fontsize = 11)
plt.ylabel('First Payment Date', fontsize = 11)
plt.title("Active Users per Month")

#формируем heatmap средней выручки с пользователя (ARPU)
plt.subplots(figsize=(14, 9))
sns.heatmap(panelArpu, annot = True, fmt='.2g', vmin = panelArpu[panelArpu > 0].min().min(), vmax = panelArpu.max().max(), mask = panelArpu < panelArpu[panelArpu > 0].min().min(), cmap = "YlOrBr")
plt.xlabel('Months after First Attraction', fontsize = 11)
plt.ylabel('Attraction Date', fontsize = 11)
plt.title("Average Revenue per User per Month (RUB `00)")

# формируем heatmap оттока пользователей
plt.subplots(figsize=(14, 9))
sns.heatmap(panelChurn, annot = True, vmin = panelChurn.min().min(), vmax = 0, robust=True, mask = panelChurn > 0, cmap = "Set1")
plt.xlabel('Months after First Attraction', fontsize = 11)
plt.ylabel('Attraction Date', fontsize = 11)
plt.title("Number of Users Leaved")