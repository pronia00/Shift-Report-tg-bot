import config

from array import array
from ast import Call
from cgitb import handler, text
from contextvars import Context
from doctest import SKIP
from email.message import Message
from glob import glob
from lib2to3.pgen2.token import STAR
from datetime import datetime
import logging
from multiprocessing.dummy import Array
from operator import truediv
from pickle import FALSE, TRUE
from tabnanny import check
from tracemalloc import start
from turtle import st
from typing import Dict, List

from uuid import uuid4
from html import escape
from xml.etree.ElementTree import Comment
from xmlrpc.client import Boolean, boolean
from aiogram import Bot

from setuptools import Command
import telegram
from telegram.constants import ParseMode

from telegram import (
    CallbackQuery,
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
    InlineQueryResultArticle,
    InputTextMessageContent
)

from telegram.ext import (
    Application,
    ContextTypes,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    InlineQueryHandler,
    ApplicationBuilder,
    CallbackContext,
    CommandHandler
)

from dataclasses import dataclass, field

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)
#consts for shift end conversation states
SE_INIT, SE_MENU, SE_DATE, SE_FINANCE, SE_PREVIEW, SE_COMMENT, SE_PRODUCTS, SE_TEAM, SE_LEFTOVERS, SE_WRITEOFFS, SE_BILLS, SE_SHIFT, SE_WITHDRAWALS, SE_STOPLIST = range(14)

#main keyboard buttons consts
_b_date = "Дата"
_b_finance = "Денюжки"
_b_leftovers = "Остатки"
_b_shift = "Кто работал"
_b_write_offs = "Списания"
_b_withdrawals = "Изъятия"
_b_stop_list = "Стоп лист"
_b_comment = "Комментарий"
_b_preview = "Предпросмотр"
_b_send = "Отправить"


_b_cash = "Наличные"
_b_cards = "Безнал"
_b_cash_returns = "Возврат наличные"
_b_cards_returns = "Возврат безнал"
_b_incass = "Инкассация"
_b_change_money = "Размен"
_b_extra_money = "Избыток / Недостача"
_b_reciept_num = "Количество чеков"
_b_all_in_one = "Заполнить все вместе"

# ✔️ ✅ 👌 🔥 ☑️ 
_b_check = "✅"

_b_milk = "Молоко"
_b_espresso_blend = "Эспрессо бленд "

_b_manual_date = "Ввести дату лапками"

_b_return = "⇐ Назад"

_b_yes = "Дяп"
_b_no = "Ноуп"

_keyboard_shift_end_main = [
        [
            InlineKeyboardButton(_b_date, callback_data = "date"),
            InlineKeyboardButton(_b_finance, callback_data = "finance")
        ],
        [
            InlineKeyboardButton(_b_write_offs, callback_data = "writeoffs"),
            InlineKeyboardButton(_b_leftovers, callback_data = "leftovers"),

        ],
        [
            InlineKeyboardButton(_b_withdrawals, callback_data = "withdrawals"),
            InlineKeyboardButton(_b_shift, callback_data = "shift")
        ], 
        [
            InlineKeyboardButton(_b_stop_list, callback_data= "stoplist"), 
            InlineKeyboardButton(_b_comment, callback_data= "comment")
        ],
        [
            InlineKeyboardButton(_b_preview, callback_data = "preview"),
        ]
    ]   

_keyboard_finance = [
    [
            InlineKeyboardButton(_b_cash, callback_data = "cash"),
            InlineKeyboardButton(_b_cards, callback_data = "cards"),
    ],
    [
            InlineKeyboardButton(_b_reciept_num, callback_data = "reciepts"),
            InlineKeyboardButton(_b_extra_money, callback_data = "extra_money")
    ],
    [
            InlineKeyboardButton(_b_incass, callback_data = "incass"),
            InlineKeyboardButton(_b_change_money, callback_data = "change_money")
    ],
    [
            InlineKeyboardButton(_b_cash_returns, callback_data = "cash_returns"),
            InlineKeyboardButton(_b_cards_returns, callback_data = "cards_returns"),
    ],
    [
            InlineKeyboardButton(_b_all_in_one, callback_data = "read_all")
    ],
    [
            InlineKeyboardButton(_b_return, callback_data = "return")
    ]
]

_keyboard_leftovers = [
    [
        InlineKeyboardButton(_b_milk, callback_data = "milk"),
        InlineKeyboardButton(_b_espresso_blend, callback_data = "espresso_blend")
    ],
    [
        InlineKeyboardButton(_b_return, callback_data = "return")
    ]
]

# leftovers subclass
@dataclass
class Leftovers:
    milk : float = 0
    is_milk : bool = False

    espresso_blend : float = 0
    is_espresso_blend : bool = False

    def is_leftovers(self) -> bool:
        return self.is_milk == self.is_espresso_blend == True

# finance data subclass 
@dataclass
class FinanceReport:
    cash : float = 0
    cards : float = 0
    
    cash_returns : float = 0
    cards_returns : float = 0
    extra : float = 0

    reciepts : int = 0

    incass : float = 0
    change : float = 5000

    is_cash : bool = False
    is_cards : bool = False
    is_cash_returns : bool = False
    is_cards_returns : bool = False
    
    is_extra : bool = False
    is_reciepts : bool = False
    is_incass : bool = False
    is_change : bool = False

    def medium_reciept(self) -> float:
        if int(self.reciepts) > 0:
            return (float(self.cash) + float(self.cards)) / int(self.reciepts) 
        else: 
            return 0

    def is_finance(self) -> bool:
        return \
            self.is_cash == self.is_cards == self.is_reciepts == self.is_incass == True

@dataclass 
class withdrawal:
    sum : float = 0
    comment : str = ''

@dataclass 
class Withdrawals:
    data : list[withdrawal] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.data) < 1
    
    def append_str(self, text : str):
        new_entry = withdrawal()
        

# storage for shift report data
@dataclass
class ShiftReportClass:

    # config data
    spot_name : str = 'More'
    result_chat : str = '-322780644'
    report_sent_by : str = 'unknown'

    # init data
    _date_created : datetime.date = datetime.today().date()
    _created_by : str = ''   # TO DO list of users spot by spot
    _is_sent : bool = False
    _initialized : bool = False

    # leftovers
    leftovers : Leftovers = Leftovers(0, False, 0, False)
    
    # finance
    finance : FinanceReport = FinanceReport()

    # date & time
    date : str = '00:00' # TO DO change to <date : datetime.date>
    is_date : bool = False

    # comment
    comment : str = ''
    is_comment : bool = False

    # writeoffs
    writeoffs : str = ''
    is_writeoffs : bool = False

    # withdrawals
    withdrawals : str = ''
    is_withdrawals : bool = False

    # shift_team
    shift_team : str = ''
    is_shift_team : bool = False

    # stop_list
    stop_list : str = ''
    is_stop_list : bool = False

    async def _init_report(self, context : ContextTypes, update : Update) : 
        self._date_created = datetime.today().date()
        self._created_by = update.effective_user.full_name
        self._initialized = True

        self.leftovers = Leftovers(0, False, 0, False)
        self.finance = FinanceReport()

@dataclass
class ShiftReport_DataBase:
    data : list[ShiftReportClass] = field(default_factory=list)
    index : int = -1

    async def get_new_report(self) -> ShiftReportClass:
        self.data.append(ShiftReportClass())
        self.index = self.index + 1
        return self.data[self.index]

    async def get_last_report(self):
        return self.data[self.index]

shift_report = ShiftReportClass()
db = ShiftReport_DataBase()

# create empty shift report class
def new_shift_report() -> ShiftReportClass :
    return ShiftReportClass()

# starts shift end conversation

async def start_conversation_menu_from_query(update:Update, context: ContextTypes):
    await start_shift_end_conversation_menu(update, context, from_query = False)
    return SE_MENU

async def start_shift_end_conversation_menu (update: Update, context: ContextTypes, from_query : bool = False) -> int:
    """Starts shift end conversation with main menu"""

    user = update.effective_user.full_name
    logger.info("User %s started the shift end converstaion", user)

    global shift_report

    # situation 1 : date is today and report is sent:
    #     -> message user that report is already sent for this date by user
    #     -> ask to: 
    #        - create new report for this date
    #        - open existing report
    #        - exit
    # 
    # situation 2 : date is today and report is not sent:
    #     -> message that report already exists and created by user
    #     -> ask to:
    #         - create new report for this date
    #         - open existing report
    #         - exit
    #
    # situation 3 : date is not today -> init new report
    #
    return_menu = SE_MENU

    # if report is new, init report and open main report menu

    logger.info(f'Shift report #{db.index} initialized by {update.effective_user.full_name}')
    logger.info(f'date = {shift_report._date_created}')
    
    _keyboard = []

    if not shift_report._initialized or not shift_report._date_created == datetime.today().date():
        logger.info(f"Creating new report for {update.effective_user.full_name}...")
        
        shift_report = await db.get_new_report()

        await shift_report._init_report(context, update)
        await draw_main_menu(update, context, edit = False)
        
        return_menu = SE_MENU

    #if report exists, and created today
    elif shift_report._date_created == datetime.today().date():
        return_menu = SE_INIT
        text = ''
        # if report in not sent
        if shift_report._is_sent == False:
            _keyboard = [
                [InlineKeyboardButton('Продолжить отчет', callback_data = "continue_report")],
                [InlineKeyboardButton('Создать новый', callback_data = 'create_new_report')], 
                [InlineKeyboardButton(_b_return, callback_data = "return")]
            ]
            
            # if report created by same user
            if shift_report._created_by == update.effective_user.full_name:
                text = 'Ты сегодня уже начал заполнять отчет, хочешь продолжить, или начать новый ?' 

            else:
                text = f'{shift_report._created_by} уже начал начал заполнять отчет, можешь продолжить его, или начать новый'
    
        # if report is already sent today
        elif shift_report._is_sent:

            _keyboard = [
                [InlineKeyboardButton('Открыть текущий отчет', callback_data = "continue_report")],
                [InlineKeyboardButton('Создать новый', callback_data = 'create_new_report')], 
                [InlineKeyboardButton(_b_return, callback_data = "return")]
            ]

            if shift_report._created_by == update.effective_user.full_name:
                text = 'Ты сегодня уже отправил отчет, хочешь открыть его, или начать новый ?' 

            else:
                text = f'{shift_report._created_by} уже отправил отчет, можешь открыть его, или начать новый'

        await draw_menu(text, _keyboard, update, context, edit = False)

    else:
        logger.info("Can't init new menu...all init conditions were skipped")
        
    return return_menu

async def init_shift_report_menu(update: Update, context: ContextTypes):
    logger.info("User %s initialised new report", update.effective_user.full_name)
    global shift_report

    shift_report = await db.get_new_report()

    await shift_report._init_report(context, update)
    
    await draw_main_menu(update, context, edit = True)

    return SE_MENU

async def continue_shift_report_menu(update: Update, context: ContextTypes):
    logger.info("User %s editing existing report", update.effective_user.full_name)

    await draw_main_menu(update, context, edit = True)
    return SE_MENU

def _check_button(b : str, check : bool) -> str:
    if (check) :
        return _b_check + ' ' + b
    return b

async def _check_buttons_main_keyboard(update: Update, context: ContextTypes) -> InlineKeyboardMarkup:
    sr = shift_report

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(_check_button(_b_date, sr.is_date), callback_data = "date"),
            InlineKeyboardButton(_check_button(_b_finance, sr.finance.is_finance()), callback_data = "finance")
        ],
        [
            InlineKeyboardButton(_check_button(_b_write_offs, sr.is_writeoffs), callback_data = "writeoffs"),
            InlineKeyboardButton(_check_button(_b_leftovers, sr.leftovers.is_leftovers()), callback_data = "leftovers"),
        ],
        [
            InlineKeyboardButton(_check_button(_b_withdrawals, sr.is_withdrawals), callback_data = "withdrawals"),
            InlineKeyboardButton(_check_button(_b_shift, sr.is_shift_team), callback_data = "shift")
        ], 
        [
            InlineKeyboardButton(_check_button(_b_stop_list, sr.is_stop_list), callback_data= "stoplist"), 
            InlineKeyboardButton(_check_button(_b_comment, sr.is_comment), callback_data= "comment")
        ],
        # add preview only if all checked ??
        [
            InlineKeyboardButton(_b_preview, callback_data = "preview"),
        ]
    ])   

async def draw_menu(text : str, buttons : InlineKeyboardMarkup, update: Update, context : ContextTypes, edit: bool):
    logger.info("Drawing menu")

    if edit == True:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            text,
            reply_markup = InlineKeyboardMarkup(buttons)
        )
    else : 
        await update.message.reply_text(
            text, 
            reply_markup = InlineKeyboardMarkup(buttons)
        )

# draws shift report menu buttons
async def draw_main_menu (update: Update, context: ContextTypes, edit: bool):

    text = "== Отчет закрытия смены ==\n\n"\
        "Выбери пункт для заполнения: "

    logger.info("Drawing main menu")

    if edit == True:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            text,
            #reply_markup = InlineKeyboardMarkup(_keyboard_shift_end_main)
            reply_markup = await _check_buttons_main_keyboard(update, context)
        )
    else :
        await update.message.reply_text(
            text, 
            reply_markup = await _check_buttons_main_keyboard(update, context)
        )

# Date
async def date_menu (update: Update, context:ContextTypes) -> int: 
    """Starts the date menu conversation """

    query = update.callback_query
    await query.answer()

    logger.info("User %s entered date menu", query.from_user.full_name)
    
    today_date_time = datetime.now().strftime("Cейчас: %d/%m %H:%M") 

    context.user_data["parent_menu"] = SE_MENU
    keyboard = [
        [InlineKeyboardButton(today_date_time, callback_data = "auto_date")], 
        [InlineKeyboardButton(_b_manual_date, callback_data = "manual_date")]
    ]

    text = "Выбери дату заполнения отчета: \n\n"
    if "date" in context.user_data:
        #_date_time = context.user_data["date"]
        _date_time = shift_report.date
    else :
        _date_time = datetime.now().strftime("%d/%m \n%H:%M")
    
    text += "Текущее значение : \n" + _date_time

    # parent const for return button navigation
    context.user_data ["parent_menu"] = SE_MENU

    await query.edit_message_text(
        text,
        reply_markup = InlineKeyboardMarkup(keyboard)
    )
    return SE_DATE

async def auto_date (update: Update, context:ContextTypes) -> int: 
    """auto fills date"""
    
    query = update.callback_query
    await query.answer()

    logger.info("User %s chose auto date", query.from_user.full_name)
    
    #context.user_data["date"] = datetime.now().strftime("%d/%m %H:%M")
    
    shift_report.date = datetime.today().date()
    shift_report.is_date = True

    await draw_main_menu(update, context, edit = True)

    return SE_MENU

async def date_input(update: Update, context:ContextTypes) -> int: 
    """read text & write into user_data"""
    
    user = update.message.from_user
    logger.info("User %s entered %s", user.full_name, update.message.text)

    #context.user_data["date"] = update.message.text
    shift_report.date = update.message.text
    shift_report.is_date = True

    await draw_main_menu(update, context, edit = False)
    
    return SE_MENU

async def manual_date (update: Update, context:ContextTypes) -> int: 
    """manual date input"""
    
    query = update.callback_query
    await query.answer()

    context.user_data["parent_menu"] = SE_DATE
    logger.info("User %s chose manual input", query.from_user.full_name)

    await query.edit_message_text(
        text = "Введи дату и время заполнения : ", 
        reply_markup 
            = InlineKeyboardMarkup([[InlineKeyboardButton(_b_return, callback_data="return")]])
    )
    return SE_DATE

# Finance

async def finance_text():
    sr = shift_report

    text = "Наличные : " + str(sr.finance.cash) + " ₽\n"
    text += "Безнал : " + str(sr.finance.cards) + " ₽\n"
    text += "Кол-во чеков : " + str(sr.finance.reciepts) + "\n\n"

    text += "Возвраты наличные : " + str(sr.finance.cash_returns) + " ₽\n"
    text += "Возвраты безнал : " + str(sr.finance.cards_returns) + " ₽\n\n"
    text += "Излишек/недостача : " + str(sr.finance.extra) + " ₽\n\n"

    text += "Инкассация : " + str(sr.finance.incass) + " ₽\n"
    text += "Размен : " + str(sr.finance.change) + " ₽\n"

    return text

async def finance_kb():
    finance = shift_report.finance
    _keyboard_finance = [
        [
                InlineKeyboardButton(_check_button(_b_cash, finance.is_cash),  callback_data = "cash"),
                InlineKeyboardButton(_check_button(_b_cards, finance.is_cards), callback_data = "cards"),
        ],
        [
                InlineKeyboardButton(_check_button(_b_reciept_num, finance.is_reciepts), callback_data = "reciepts"),
                InlineKeyboardButton(_check_button(_b_extra_money, finance.is_extra), callback_data = "extra_money")
        ],
        [
                InlineKeyboardButton(_check_button(_b_incass, finance.is_incass), callback_data = "incass"),
                InlineKeyboardButton(_check_button(_b_change_money, finance.is_change), callback_data = "change_money")
        ],
        [
                InlineKeyboardButton(_check_button(_b_cash_returns, finance.is_cash_returns), callback_data = "cash_returns"),
                InlineKeyboardButton(_check_button(_b_cards_returns, finance.is_cards_returns), callback_data = "cards_returns"),
        ],
        [
                InlineKeyboardButton(_b_all_in_one, callback_data = "read_all")
        ],
        [
                InlineKeyboardButton(_b_return, callback_data = "return")
        ]
    ]
    return InlineKeyboardMarkup(_keyboard_finance)


async def finance_menu (update: Update, context:ContextTypes) -> int: 
    """Starts the date menu conversation """

    query = update.callback_query
    await query.answer()

    data = ["cash", "cards", "reciepts", "cash_returns", "cards_returns", "incass", "change_money", "extra_money"]
    logger.info(f"User {query.from_user.full_name} entered finance report menu" )

    await query.edit_message_text(
        await finance_text(),
        reply_markup = await finance_kb()
    )
    return SE_FINANCE

async def draw_finance_menu (update: Update, context:ContextTypes) -> int: 
    """ Shows data values and send finance menu keyboard """    

    data = ["cash", "cards", "reciepts", "cash_returns", "cards_returns", "incass", "change_money", "extra_money"]
    logger.info("Draw finance menu")
    logger.info("User %s entered finance report menu", update.message.from_user.full_name)

    # parent const for return button navigation
    context.user_data ["parent_menu"] = SE_MENU

    await update.message.reply_text(
        await finance_text(),
        reply_markup = await finance_kb()
    )

async def finance_field (update: Update, context: ContextTypes) -> int:
    query = update.callback_query
    await query.answer()
    
    logger.info("User %s chose %s", query.from_user.full_name, query.data)
    context.user_data["finance_entry"] = query.data

    context.user_data["parent_menu"] = SE_FINANCE

    # вывод сообщения о вводе значения
    await query.edit_message_text(
        "Введи значение : ",
        reply_markup= InlineKeyboardMarkup([[InlineKeyboardButton(_b_return, callback_data="return")]])
    )
    return SE_FINANCE

async def finance_field_input (update: Update, context: ContextTypes) -> int:
    user = update.message.from_user

    #here you can catch the <all in one> query, and send it to func - parser
    if (context.user_data["finance_entry"] == "read_all"):
        #parse(update.message.text)
        values = ["cash", "cards", "incass", "reciepts"]
        list_of_values = update.message.text.splitlines()

        logger.info("User %s entered values: \n%s", user.full_name, update.message.text)
        
        #bug - only all lines input is valid (((
        for x in [0, 1, 2, 3]:
            context.user_data[values[x]] = list_of_values[x]

        shift_report.finance.cash = list_of_values[0]
        shift_report.finance.cards = list_of_values[1]
        shift_report.finance.incass = list_of_values[2]
        shift_report.finance.reciepts = list_of_values[3]

        shift_report.finance.is_cash = True 
        shift_report.finance.is_cards = True
        shift_report.finance.is_incass = True
        shift_report.finance.is_reciepts = True

    else: 
        logger.info("User %s entered %s = %s", user.full_name, context.user_data["finance_entry"], update.message.text)
        

        entry = context.user_data["finance_entry"]
        data = float(update.message.text)

        if entry == 'cash':
            shift_report.finance.cash = data
            shift_report.finance.is_cash = True

        elif entry == 'cards':
            shift_report.finance.cards = data
            shift_report.finance.is_cards = True

        elif entry == 'reciepts':
            shift_report.finance.reciepts = data
            shift_report.finance.is_reciepts = True
            
        elif entry == 'incass':
            shift_report.finance.incass = data
            shift_report.finance.is_incass = True
            
        elif entry == 'cash_returns':
            shift_report.finance.cash_returns = data
            shift_report.finance.is_cash_returns = True

        elif entry == 'cards_returns':
            shift_report.finance.cards_returns = data
            shift_report.finance.is_cards_returns = True

        elif entry == 'change_money': 
            shift_report.finance.change = data
            shift_report.finance.is_change = True
        
        elif entry == 'extra_money':
            shift_report.finance.extra = data
            shift_report.finance.is_extra = True

        #context.user_data[context.user_data["finance_entry"]] = update.message.text
    await draw_finance_menu(update, context)

    return SE_FINANCE

async def finance_read_all(update: Update, context:ContextTypes) -> int: 
    """gets "заполнить все поля" callback.query && send explanational messasage how to reply"""

    query = update.callback_query
    await query.answer()

    context.user_data["parent_menu"] = SE_FINANCE
    context.user_data["finance_entry"] = query.data

    # можно динамический сформировать текст                 
    text = "Введи цифровые значения в таком порядке, каждое в новой строке: \n\n"
    text += "Выручка наличными (" + str(shift_report.finance.cash) + "₽) \n"
    text += "Выручка по картам (" + str(shift_report.finance.cards) + "₽) \n"
    text += "Инкассация (" + str(shift_report.finance.incass) + "₽) \n"
    text += "Количество чеков (" + str(shift_report.finance.reciepts) + "шт) \n\n"
    text += "Остальные значения, при необоходимости, можно ввести по отдельности в меню фин отчета\n"
    text += "Значение размена по умолчанию равно 5000"

    await query.edit_message_text(
        text,
        reply_markup= InlineKeyboardMarkup([[InlineKeyboardButton(_b_return, callback_data="return")]])
    )
    return SE_FINANCE

# Comment
async def comment_menu(update: Update, context: ContextTypes) -> int: 
    query = update.callback_query
    await query.answer()

    logger.info("User %s entered comments menu", query.from_user.full_name)

    context.user_data["parent_menu"] = SE_MENU

    text = "Отправь комментарий о смене: \n"
    if shift_report.is_comment:
        text += "Текущий комментарий:\n\n" + shift_report.comment

    await query.edit_message_text(
        text, 
        reply_markup= InlineKeyboardMarkup([[InlineKeyboardButton(_b_return, callback_data="return")]])
    )
    return SE_COMMENT

async def read_comment(update: Update, context: ContextTypes) -> int:
    """reads comment from last user's message"""
    
    shift_report.comment = update.message.text
    shift_report.is_comment = True

    logger.info("User %s entered: %s\n", update.message.from_user.full_name, update.message.text)
    await draw_main_menu(update, context, edit=False)

    return SE_MENU


# Writeoffs
async def writeoffs_menu(update: Update, context: ContextTypes) -> int: 
    query = update.callback_query
    await query.answer()

    logger.info("User %s entered writeoffs menu", query.from_user.full_name)

    context.user_data["parent_menu"] = SE_MENU
    
    text = "Отправь списания за смену в формате:  \n\n"
    text += "Продукт 1 - количество - причина\n"
    text += "Продукт 2 - колzичество - причина\n  ..."

    if shift_report.is_writeoffs:
        text += "\n\nТекущие списания:\n" + shift_report.writeoffs
        # тут можно узнать у пользователя, хочет ли он добавить что то к текущей записи, или переписать 

    await query.edit_message_text(
        text, 
        reply_markup= InlineKeyboardMarkup([[InlineKeyboardButton(_b_return, callback_data="return")]])
    )
    return SE_WRITEOFFS

async def read_writeoffs(update: Update, context: ContextTypes) -> int:
    """reads writeoffs from last user's message"""
    
    shift_report.writeoffs = update.message.text
    shift_report.is_writeoffs = True

    logger.info("User %s entered:\n%s", update.message.from_user.full_name, shift_report.writeoffs)
    await draw_main_menu(update, context, edit=False)

    return SE_MENU


# Withdrawals
async def withdrawals_menu(update: Update, context: ContextTypes) -> int: 
    query = update.callback_query
    await query.answer()

    logger.info("User %s entered withdrawals menu", query.from_user.full_name)

    context.user_data["parent_menu"] = SE_MENU

    text = "Отправь изьятия за смену в формате:  \n\n"
    text += "Поставщик 1 - Сумма\n"
    text += "Поставщик 2 - Сумма\n..."

    if shift_report.is_withdrawals:
        text += "\n\nТекущие списания:\n" + shift_report.withdrawals
        # тут можно узнать у пользователя, хочет ли он добавить что то к текущей записи, или переписать 

    await query.edit_message_text(
        text, 
        reply_markup= InlineKeyboardMarkup([[InlineKeyboardButton(_b_return, callback_data="return")]])
    )
    return SE_WITHDRAWALS

async def read_withdrawals(update: Update, context: ContextTypes) -> int:
    """reads withdrawals from last user's message"""
    
    shift_report.withdrawals = update.message.text
    shift_report.is_withdrawals = True

    logger.info("User %s entered:\n%s", update.message.from_user.full_name, shift_report.withdrawals)
    await draw_main_menu(update, context, edit=False)

    return SE_MENU


# Stoplist
async def stoplist_menu(update: Update, context: ContextTypes) -> int: 
    query = update.callback_query
    await query.answer()

    logger.info("User %s entered stop list menu", query.from_user.full_name)

    context.user_data['parent_menu'] = SE_MENU

    text = "Заполни стоп лист в любом формате:"

    if shift_report.is_stop_list:
        text += f"\n\nСтоп лист:\n {str(shift_report.stop_list)}"
        # тут можно узнать у пользователя, хочет ли он добавить что то к текущей записи, или переписать 

    await query.edit_message_text(
        text, 
        reply_markup= InlineKeyboardMarkup([[InlineKeyboardButton(_b_return, callback_data="return")]])
    )
    return SE_STOPLIST

async def read_stoplist(update: Update, context: ContextTypes) -> int:
    # жесткое дублирование чтения в стоп листе, списаниях и изъятиях
    """reads stop list from last user's message"""
    
    shift_report.stop_list = update.message.text
    shift_report.is_stop_list = True

    logger.info("User %s entered:\n%s", update.message.from_user.full_name, shift_report.stop_list)
    await draw_main_menu(update, context, edit=False)

    return SE_MENU  



# Leftovers
async def leftovers_menu(update: Update, context: ContextTypes) -> int:
    query = update.callback_query
    await query.answer()

    logger.info("user %s entered leftovers menu", query.from_user.full_name)
    
    context.user_data["parent_menu"] = SE_MENU

    #if "milk" not in context.user_data:
    #    context.user_data["milk"] = 0
    #if "espresso_blend" not in context.user_data:
    #    context.user_data["espresso_blend"] = 0
    
    text = "Количество остатков: \n\n"
    text += "Молоко: " + str(shift_report.leftovers.milk) + "л\n"
    text += "Эспрессо блэнд: " + str(shift_report.leftovers.espresso_blend) + "кг\n"

    _keyboard_leftovers = await _leftovers_keyboard()

    await query.edit_message_text(
        text,
        reply_markup = InlineKeyboardMarkup(_keyboard_leftovers)
    )
    return SE_LEFTOVERS

async def draw_leftovers_menu (update: Update, context:ContextTypes) -> int: 
    """ Shows data values and send leftovers menu keyboard """    

    logger.info("Return to leftovers menu")
    logger.info("User %s entered leftovers report menu", update.message.from_user.full_name)

    context.user_data["parent_menu"] = SE_MENU   

    text = "Количество остатков: \n\n"
    text += "Молоко: " + str(shift_report.leftovers.milk) + "л\n"
    text += "Эспрессо блэнд: " + str(shift_report.leftovers.espresso_blend) + "кг\n"

    # parent const for return button navigation
    context.user_data ["parent_menu"] = SE_MENU

    leftovers = shift_report.leftovers

    _keyboard_leftovers = await _leftovers_keyboard()

    await update.message.reply_text(
        text,
        reply_markup = InlineKeyboardMarkup(_keyboard_leftovers)
    )


async def _leftovers_keyboard():
    leftovers = shift_report.leftovers
    return [
        [
            InlineKeyboardButton(_check_button(_b_milk, leftovers.is_milk), callback_data = "milk"),
            InlineKeyboardButton(_check_button(_b_espresso_blend, leftovers.is_espresso_blend), callback_data = "espresso_blend")
        ],
        [
            InlineKeyboardButton(_b_return, callback_data = "return")
        ]
    ]
  
async def leftovers_field (update: Update, context: ContextTypes) -> int:
    query = update.callback_query
    await query.answer()
     
    logger.info("User %s chose %s", query.from_user.full_name, query.data)
    context.user_data["leftovers_entry"] = query.data

    context.user_data["parent_menu"] = SE_LEFTOVERS

    # вывод сообщения о вводе значения
    await query.edit_message_text(
        "Введи значение : ",
        reply_markup= InlineKeyboardMarkup([[InlineKeyboardButton(_b_return, callback_data="return")]])
    )
    return SE_LEFTOVERS

async def leftovers_field_input (update: Update, context: ContextTypes):
    user = update.message.from_user
    
    logger.info("User %s entered %s = %s", user.full_name, context.user_data["leftovers_entry"], update.message.text)
    
    #context.user_data[context.user_data["leftovers_entry"]] = update.message.text
    
    if (context.user_data["leftovers_entry"] == 'milk'):
        shift_report.leftovers.milk = float(update.message.text)
        shift_report.leftovers.is_milk = True

    elif (context.user_data['leftovers_entry'] == 'espresso_blend'):
        shift_report.leftovers.espresso_blend = float(update.message.text)
        shift_report.leftovers.is_espresso_blend = True

    #if ('milk' in context.user_data) and ('espresso_blend' in context.user_data):
    #   context.user_data['check_leftovers'] = True
    
    await draw_leftovers_menu(update, context)


# Shift
async def shift_menu (update: Update, context:ContextTypes) -> int: 
    """ enter shift data """

    query = update.callback_query
    await query.answer()

    context.user_data["parent_menu"] = SE_MENU
    logger.info("User %s chose shift table menu", query.from_user.full_name)

    text = "Введи кто был на смене в формате:\n Имя 1 - Часы\n Имя 2 - Часы\n"
    
    if shift_report.is_shift_team:
        text += "Текущая инфа: \n" + shift_report.shift_team

    await query.edit_message_text(
        text, 
        reply_markup
            = InlineKeyboardMarkup([[InlineKeyboardButton(_b_return, callback_data="return")]])
    )
    return SE_SHIFT

async def shift_input(update: Update, context:ContextTypes) -> int: 
    """read text & write into user_data"""
    
    user = update.message.from_user
    logger.info("User %s entered %s", user.full_name, update.message.text)

    shift_report.shift_team = update.message.text
    shift_report.is_shift_team = True

    await draw_main_menu(update, context, edit = False)

    return SE_MENU

# Send message to chat
async def message(update, context, text = ""):
    chat = -322780644
    msg = await context.bot.send_message( chat_id= chat,text= text, parse_mode='HTML')

    return msg

async def check_data(update, context):
    data = ['date', 'finance', 'writeoffs', 'leftovers', 'withdrawals', 'shift', 'stoplist', 'comment']

    for field in data:
        if ('check_' + field) not in context.user_data:
            return False
    
    return True

# Create and send report to chat
async def send_report(update: Update, context: ContextTypes) -> int:
    """Send final report"""

    query = update.callback_query
    await query.answer()

    logger.info("User %s chose to send report", query.from_user.full_name)
    chat = config.SURF_X_MORE_CHAT

    #await context.bot.send_chat_action(chat_id= chat, action=telegram.constants.ChatAction.TYPING)
    
    # header
    text = "<b>==== Очет закрытия смены ====</b> \n"
    
    # date and time
    text += "\n⌚<b>Дата заполнения:</b> " + shift_report.date + "\n"
    
    # finance report
    text += "\n<b>Финансовый отчет: </b>\n"
    text += "💵 <b>Наличные: </b>" + str(shift_report.finance.cash) + " ₽\n"
    text += "💳 <b>Карты: </b>" + str(shift_report.finance.cards) + " ₽\n\n"
    
    text += "🧾 <b>Чеки: </b>" + str(shift_report.finance.reciepts) + "  "
    text += "🤑 <b>Средний: </b>" + str(shift_report.finance.medium_reciept()) + ' ₽\n\n'
    
    text += "💰<b>Инкассация: </b>" + str(shift_report.finance.incass) + " ₽\n"
    text += "🪙<b>Размен: </b>" + str(shift_report.finance.change) + " ₽\n\n"
    
    if (shift_report.finance.is_cash_returns):
        text += '\n<b>Возвраты наличных: </b>' + str(shift_report.finance.cash_returns) + ' ₽\n'
        
    if (shift_report.finance.is_cards_returns):
        text += '\n<b>Возвраты по картам: </b>' + str(shift_report.finance.cards_returns) + ' ₽\n'
    
    await message(update, context, text = text)

    # withdrawals data
    text = "🗒️ <b>Изъятия:</b>\n"
    text += shift_report.withdrawals
    
    #parse by lines and add tabs
    #lines = str(context.user_data["withdrawals"]).splitlines()
    #for line in lines: text += "    " + line + "\n"

    # writeoffs data
    text += "\n\n💀 <b>Списания:</b>\n"
    text += str(shift_report.writeoffs)

    # leftovers data
    text += "\n\n<b>Остатки продуктов:</b>\n"
    text += "🥛 <b>Молоко: </b>" + str(shift_report.leftovers.milk) + " л\n"
    text += "🫘 <b>Блэнд: </b>" + str(shift_report.leftovers.espresso_blend) + " кг\n"
    await message(update, context, text = text)
    
    # stop list data
    text = "\n⛔ <b>Стоп лист:</b>\n"
    text += shift_report.stop_list
    await message(update, context, text = text)
    
    # shift data
    text = "🏄‍♂️ <b>Работку работали:</b>\n"
    text += shift_report.shift_team
    await message(update, context, text = text)
    
    # comment
    text = "💬<b>Комментарий:</b>\n"
    text += shift_report.comment
    
    # who sent report-user.full_name
    text += "\n\n🙋‍♂️Заполнил - " + update.effective_user.full_name
    await message(update, context, text = text)

    context.user_data["parent_menu"] = SE_MENU

    await query.edit_message_text(
        'Отчет отправлен :3'
    )
    
    shift_report._is_sent = True
    #await shift_report_to_zero()    

    logger.info("Report is sent")
    logger.info("Shift report conversation completed")

    return ConversationHandler.END

async def shift_report_to_zero():
    global shift_report
    new_shift_report = ShiftReportClass()
    shift_report = new_shift_report
    logger.info('Shift report object is set to zero')



# Draw report preview for user
async def preview_report(update: Update, context: ContextTypes) -> int:
    """Show report"""
    
    query = update.callback_query

    context.user_data["parent_menu"] = SE_MENU

    #fast check if data exist and return data of 'none' 
    data_or_x = lambda x : 'none' if ('check_' + x) not in data else data[x]

    logger.info("User %s chose preview", query.from_user.full_name)
    text = "Предпросмотр отчета смены: \n"
    
    data = context.user_data

    text += "\n⌚Дата заполнения: " + shift_report.date + "\n"
    
    text += "\nФинансовый отчет: \n"
    text += "💵 Наличные: " + str(shift_report.finance.cash) + " ₽\n"
    text += "💳 Карты: " + str(shift_report.finance.cards) + " ₽\n\n"
    
    text += "🧾 Чеки: " + str(shift_report.finance.reciepts) + "  "
    text += "🤑 Средний: " + str(shift_report.finance.medium_reciept())
    
    text += "💰Инкассация: " + str(shift_report.finance.incass) + " ₽\n"
    text += "🪙Размен: " + str(shift_report.finance.change) + " ₽\n\n"
    
    if (shift_report.finance.is_cash_returns):
        text += 'Возвраты наличных: ' + str(shift_report.finance.cash_returns) + ' ₽\n'
    if (shift_report.finance.is_cards_returns):
        text += '\nВозвраты по картам: ' + str(shift_report.finance.cards_returns) + ' ₽\n'
    
    # withdrawals data
    text += "\n🗒️Изъятия за день:\n"
    text += shift_report.withdrawals
    
    #parse by lines and add tabs
    #lines = str(context.user_data["withdrawals"]).splitlines()
    #for line in lines: text += "    " + line + "\n"

    # writeoffs data
    text += "\n\n💀Списания за день:\n"
    text += shift_report.writeoffs

    # leftovers data
    text += "\n\nОстатки продуктов:\n"
    text += "  🥛Молоко: " + str(shift_report.leftovers.milk) + " л\n"
    text += "  🫘Блэнд: " + str(shift_report.leftovers.espresso_blend) + " кг\n"
    
    # stop list data
    text += "\n⛔Стоп лист:\n"
    text += shift_report.stop_list
    
    # shift data
    text += "\n\n🏄‍♂️В смене отработали человечки:\n"
    text += shift_report.shift_team
    
    # comment
    text += "\n\n💬Комментарий о смене:\n"
    text += shift_report.comment
    

    # who sent report
    shift_report.report_sent_by = update.effective_user.full_name
    text += "\n\n🙋‍♂️Заполнил - " + shift_report.report_sent_by
    
    await query.answer()
    await query.edit_message_text(
        text, 
        reply_markup
            = InlineKeyboardMarkup([[
                InlineKeyboardButton("Отправить отчет", callback_data="send_report"),
                InlineKeyboardButton(_b_return, callback_data="return")]])
    )

    return SE_PREVIEW

async def start_command(update: Update, context: ContextTypes):
    
    logger.info(f"\start {update.effective_user.full_name} entered \start command")

    msg = 'Привет!\n\n'
    msg += 'Этот бот поможет тебе заполнить отчет закрытия смены, и поделиться им с командой\n\n'
    msg += 'После заполнения отчет будет отправлен в ваш общий чат\n\n'
    msg += 'Начать - /shift_end \n'
    msg += 'Закрыть отчет - /cancel'
    
    '''
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton('Создать отчет по смене', callback_data='start_shift_end_from_start_button')
        ]
    ])
    '''
    await update.message.reply_text(msg)


async def help_command(update: Update, context: ContextTypes):
    logger.info(f"/help - user {update.effective_user.full_name} entered /help command")

    msg =  'Бот закрытия смены, который должен сделать жизнь чуть чуть проще\n\n'
    msg += 'Если нужна какая то помощь, или фидбек, пиши сюды: @fruqube\n\n'
    msg += 'Проект где на уровне альфы, так что пользуйся осторожно\n'

    await update.message.reply_text(msg)

# if user tries /cancel out of conversation
async def cancel_command(update: Update, context: ContextTypes):
    logger.info(f'/cancel - user {update.effective_user.full_name} entered /cancel out of conversation')

    msg =  'Эта команда работает только во время заполнения отчета /shift_end \nТак что сейчас ничего не произошло'
    await update.message.reply_text(msg)

async def unknown_command(update: Update, context: ContextTypes):
    logger.info(f'{update.message.text} - user {update.effective_user.full_name} entered unknown command')
    
    msg =  'Я не знаю эту комманду, нажми /help, если не уверен что делать'
    await update.message.reply_text(msg)

# return to menu switch
async def return_button(update: Update, context:ContextTypes) -> int:
    await update.callback_query.answer()

    parent = context.user_data["parent_menu"]
    logger.info("Parent = %s", parent)

    if parent == SE_MENU:
        await draw_main_menu(update, context, edit = True)

    if parent == SE_DATE:
        await date_menu(update, context)

    if parent == SE_FINANCE:
        await finance_menu(update, context)

    if parent == SE_LEFTOVERS:
        await leftovers_menu(update, context)

    return parent

async def decision_menu(update: Update, context:ContextTypes) -> int:
    query = update.callback_query
    await query.answer()

    parent = context.user_data["parent_menu"]
    
    logger.info(f"User {query.message.from_user.full_name} entered decision menu with parent {parent}")

    await query.edit_message_text(
        "Отправить отчет в чат ?", 
        reply_markup
            = InlineKeyboardMarkup([[
                InlineKeyboardButton("Да", callback_data="yes"),
                InlineKeyboardButton("Нет", callback_data="return")]])
    )
    return SE_PREVIEW

# Cancel end exit shift report
async def cancel(update: Update, context:ContextTypes) -> int: 
    """cancel report"""
    logger.info("User %s canceled report menu", update.effective_user.full_name)

    await update.message.reply_text("Ты вышел из меню заполнения отчета, он сохранен, но не отправлен\nЕсли решишь продолжить заполнение, просто снова нажми /shift_end")

    return ConversationHandler.END

async def __shift_end_report__ () :
    return 0

def main() -> None: 
    """Run the bot."""

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(config.BOT_TOKEN).build()

    # ^ means "start of line/string"
    # $ means "end of line/string"
    # So ^ABC$ will only allow 'ABC'

    zero_shift_end = ShiftReportClass()

    end_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("shift_end", start_shift_end_conversation_menu), 
            CallbackQueryHandler(start_conversation_menu_from_query, pattern = '^' + 'start_shift_end_from_start_button' + '$')
            ],
        states= {
            SE_INIT : [
                CallbackQueryHandler(init_shift_report_menu, pattern="^" + "create_new_report" + "$"),
                CallbackQueryHandler(continue_shift_report_menu, pattern="^" + "continue_report" + "$")
            ],
            SE_MENU : [
                CallbackQueryHandler(finance_menu, pattern = "^" + "finance" + "$"),
                CallbackQueryHandler(date_menu, pattern = "^" + "date" + "$"),
                CallbackQueryHandler(comment_menu, pattern = "^" + "comment" + "$"),
                CallbackQueryHandler(leftovers_menu, pattern = "^" + "leftovers"),
                CallbackQueryHandler(shift_menu, pattern = "^" + "shift"), 
                CallbackQueryHandler(preview_report, pattern = "^" + "preview"), 
                CallbackQueryHandler(writeoffs_menu, pattern = "^" + "writeoffs" + "$"),
                CallbackQueryHandler(withdrawals_menu, pattern = "^" + "withdrawals" + "$"),
                CallbackQueryHandler(stoplist_menu, pattern = "^" + "stoplist" + "$")
            ],
            SE_DATE : [
                CallbackQueryHandler(auto_date, pattern="^" + "auto_date" + "$"),
                CallbackQueryHandler(manual_date, pattern="^" + "manual_date" + "$"),
                MessageHandler(filters.TEXT & (~filters.COMMAND), date_input)
            ],
            SE_FINANCE: [
                CallbackQueryHandler(return_button, pattern="^" + "return" + "$"),
                CallbackQueryHandler(finance_read_all, pattern="^" + "read_all" + "$"),
                CallbackQueryHandler(finance_field) ,
                MessageHandler(filters.TEXT & (~filters.COMMAND), finance_field_input)
            ],
            SE_PREVIEW: [
                CallbackQueryHandler(decision_menu, pattern="^" + "send_report" + "$"),
                CallbackQueryHandler(send_report, pattern="^" + "yes" + "$")            ],
            SE_COMMENT: [
                MessageHandler(filters.TEXT & (~filters.COMMAND), read_comment)
            ],
            SE_LEFTOVERS: [
                CallbackQueryHandler(leftovers_field, pattern = "^" + "milk" + "$"),
                CallbackQueryHandler(leftovers_field, pattern = "^" + "espresso_blend" + "$"),
                MessageHandler(filters.TEXT & (~filters.COMMAND), leftovers_field_input)
            ],
            SE_SHIFT: [
                MessageHandler(filters.TEXT & (~filters.COMMAND), shift_input)
            ],
            SE_WRITEOFFS: [
                MessageHandler(filters.TEXT & (~filters.COMMAND), read_writeoffs)
            ],
            SE_WITHDRAWALS: [
                MessageHandler(filters.TEXT & (~filters.COMMAND), read_withdrawals)
            ],
            SE_STOPLIST: [
                MessageHandler(filters.TEXT & (~filters.COMMAND), read_stoplist)
            ]
        },
        fallbacks=[
            CallbackQueryHandler(return_button, pattern="^" + "return" + "$"),

            CommandHandler('shift_end', start_shift_end_conversation_menu),
            CommandHandler("cancel", cancel)
        ],
    )

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('help', help_command))
    #application.add_handler(MessageHandler(filters.Command, unknown_command))
    #application.add_handler(CommandHandler('test', test))

    #application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo))
    application.add_handler(end_conv_handler)
    application.add_handler(CommandHandler('cancel', cancel_command))
     # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()

