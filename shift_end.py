from socket import MsgFlag
import config

from array import array
from ast import Call, parse
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

_report_header = 'Отчет по смене'
# ✔️ ✅ 👌 🔥 ☑️ 
_b_check = "✅"

_b_milk = "Молоко"
_b_espresso_blend = "Эспрессо бленд "

_b_manual_date = "Другая дата"

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
    comment : str = ''
    sum : float = 0

@dataclass
class writeoff:
    product : str = ''
    quantity : float = 0
    comment : str = ''


# create parent @dataclass for Writeoffs and Withdrawals
@dataclass
class Writeoffs:
    data : list[writeoff] = field(default_factory=list)
    _rewrite : bool = True

    def is_empty(self) -> bool:
        return len(self.data) < 1

    def quantity(self) -> int:
        return len(self.data)

    async def append(self, product : str, quantity : float, comment : str):
        self.data.append(withdrawal(product, quantity, comment))
    
    async def append(self, entry : writeoff):
        self.data.append(entry)
    
    async def set_to_zero(self):
        self.data.clear()

    async def append_str(self, text : str) -> bool:
        try:
            parsed_data = text.split('-')
        except ValueError:
            return False

        if len(parsed_data) < 3:
            return False

        for x in parsed_data:
            if x == '':
                return False
        try: 
            float(parsed_data[1])

        except ValueError:
            return False

        new_entry = writeoff(str(parsed_data[0]), float(parsed_data[1]), str(parsed_data[2]))
        await self.append(new_entry)

        return True

    def to_report_text(self) -> str:
        msg = ''
        if len(self.data) <= 0:
            msg += '🗒️ <b>Списаний нет</b> \n'
        else:
            msg += "🗒️ <b>Списания:</b>\n"
            num = 1
            for w in shift_report._writeoffs.data:
                msg += f'{num}. {w.product} - {num_to_str(w.quantity)} - {w.comment} \n'
                num = num + 1
        return msg

        
@dataclass 
class Withdrawals:
    data : list[withdrawal] = field(default_factory=list)
    _rewrite : bool = True

    def is_empty(self) -> bool:
        return len(self.data) < 1
    
    def quantity(self) -> int: 
        return len(self.data)

    async def append_str(self, text : str) -> bool:
        parsed_data = text.partition('-')
        if parsed_data[1] == '' and str(parsed_data[2]) == '': return False
        if parsed_data[0] == '' or parsed_data[2] == '': return False
        
        try:
            float(parsed_data[2])
            
        except ValueError:
            return False

        new_entry = withdrawal(str(parsed_data[0]), float(parsed_data[2]))
        await self.append(new_entry)
        
        return True

    async def append(self, comment : str, sum : float):
        self.data.append(withdrawal(comment, sum))
    
    async def append(self, entry : withdrawal):
        self.data.append(entry)

    async def set_to_zero(self):
        self.data.clear()

    def to_report_text(self) -> str:
        text = ''
        if len(self.data) <= 0:
            text += '🗒️ <b>Изъятий нет</b> \n'
        else:
            text += "🗒️ <b>Изъятия:</b> \n"
            i = 1
            for w in self.data:
                text += f'  {i}. {w.comment} - {num_to_str(w.sum)}р\n'
                i = i + 1
        
        return text

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
    date : str = '01.01.01' # TO DO change to <date : datetime.date>
    is_date : bool = False

    # comment
    comment : str = ''
    is_comment : bool = False

    # writeoffs
    _writeoffs : Writeoffs = Writeoffs()

    writeoffs : str = ''
    is_writeoffs : bool = False

    # withdrawals
    _withdrawals : Withdrawals = Withdrawals()

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
        self._withdrawals = Withdrawals()
        self._writeoffs = Writeoffs()

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

    global shift_report
    return_menu = SE_MENU

    # if report is new, init report and open main report menu
    logger.info(f"User {update.effective_user.full_name} initialized shift end converstaion")
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
            reply_markup = InlineKeyboardMarkup(buttons), 
            parse_mode='HTML'
        )
    else : 
        await update.message.reply_text(
            text, 
            reply_markup = InlineKeyboardMarkup(buttons), 
            parse_mode='HTML'
        )

# draws shift report menu buttons
async def draw_main_menu (update: Update, context: ContextTypes, edit: bool):

    text = f'<b>Отчет по смене  |  Surf Coffee x {shift_report.spot_name}</b>'
    logger.info("Drawing main menu")

    if edit == True:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            text,
            #reply_markup = InlineKeyboardMarkup(_keyboard_shift_end_main)
            reply_markup = await _check_buttons_main_keyboard(update, context),
            parse_mode='HTML'
        )
    else :
        await update.message.reply_text(
            text,
            reply_markup = await _check_buttons_main_keyboard(update, context),
            parse_mode='HTML'
        )

# Date
async def date_menu (update: Update, context:ContextTypes) -> int: 
    """Starts the date menu conversation """

    query = update.callback_query
    await query.answer()

    logger.info(f"User {query.from_user.full_name} entered date menu")
    
    today_date_time = datetime.now().strftime("Сегодня") 

    context.user_data["parent_menu"] = SE_MENU
    keyboard = [
        [InlineKeyboardButton(today_date_time, callback_data = "auto_date"), 
        InlineKeyboardButton('Другой день', callback_data = "manual_date")],
        [InlineKeyboardButton(_b_return, callback_data = 'return')]
    ]

    text = f'<b>Выбери дату заполнения:   </b>\n\n'
    if "date" in context.user_data:
        _date_time = shift_report.date
    else :
        _date_time = datetime.today().date()
    
    #text += f'Текущее значение : { str(_date_time)}'

    # parent const for return button navigation
    context.user_data ["parent_menu"] = SE_MENU

    await query.edit_message_text(
        text,
        reply_markup = InlineKeyboardMarkup(keyboard), 
        parse_mode = 'HTML'
    )
    return SE_DATE

async def auto_date (update: Update, context:ContextTypes) -> int: 
    """auto fills date"""
    
    query = update.callback_query
    await query.answer()

    logger.info(f"User {query.from_user.full_name} chose <auto> date input")
        
    shift_report.date = datetime.today().date()
    shift_report.is_date = True

    await draw_main_menu(update, context, edit = True)

    return SE_MENU

async def date_input(update: Update, context:ContextTypes) -> int: 
    """read text & write into user_data"""
    
    user = update.message.from_user
    logger.info(f"User {update.effective_user.full_name} entered: {update.message.text}")

    shift_report.date = update.message.text
    shift_report.is_date = True

    await draw_main_menu(update, context, edit = False)
    return SE_MENU

async def manual_date (update: Update, context:ContextTypes) -> int: 
    """manual date input"""
    
    query = update.callback_query
    await query.answer()
    
    logger.info(f"User {query.from_user.full_name} chose manual input")

    context.user_data["parent_menu"] = SE_DATE

    await query.edit_message_text(
        text = "<b>Введи дату заполнения: </b> ", 
        reply_markup 
            = InlineKeyboardMarkup([[InlineKeyboardButton(_b_return, callback_data='return')]]),
            parse_mode = 'HTML'
    )
    return SE_DATE

# Finance
async def finance_text():
    sr = shift_report

    text = '<b>Выбери и заполни финансы: </b>\n\n'
    text += "Наличные : " + str(sr.finance.cash) + " ₽\n"
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
    logger.info(f"User {update.effective_user.full_name} entered finance report menu" )
    
    query = update.callback_query
    await query.answer()

    data = ["cash", "cards", "reciepts", "cash_returns", "cards_returns", "incass", "change_money", "extra_money"]
    context.user_data ["parent_menu"] = SE_MENU

    await query.edit_message_text(
        await finance_text(),
        reply_markup = await finance_kb(),
        parse_mode='HTML'
    )
    return SE_FINANCE

async def draw_finance_menu (update: Update, context:ContextTypes) -> int: 
    """ Shows data values and send finance menu keyboard """    
    logger.info("Drawing finance menu")
    logger.info(f"User {update.effective_user.full_name} entered finance report menu")
    
    data = ["cash", "cards", "reciepts", "cash_returns", "cards_returns", "incass", "change_money", "extra_money"]

    # parent const for return button navigation
    context.user_data ["parent_menu"] = SE_MENU

    await update.message.reply_text(
        await finance_text(),
        reply_markup = await finance_kb(), 
        parse_mode='HTML'
    )

async def finance_field (update: Update, context: ContextTypes) -> int:
    query = update.callback_query
    await query.answer()
    
    logger.info("User %s chose %s", query.from_user.full_name, query.data)
    context.user_data["finance_entry"] = query.data

    context.user_data["parent_menu"] = SE_FINANCE

    # вывод сообщения о вводе значения
    await query.edit_message_text(
        "<b>Введи значение : </b>",
        reply_markup= InlineKeyboardMarkup([[InlineKeyboardButton(_b_return, callback_data="return")]]),
        parse_mode='HTML'
    )
    return SE_FINANCE

async def finance_field_input (update: Update, context: ContextTypes) -> int:
    user = update.message.from_user

    context.user_data["parent_menu"] = SE_FINANCE
    try:
        #here you can catch the <all in one> query, and send it to func - parser
        if (context.user_data["finance_entry"] == "read_all"):
            #parse(update.message.text)
            values = ["cash", "cards", "incass", "reciepts"]
            list_of_values = update.message.text.splitlines()

            logger.info(f'User {update.effective_user.full_name} entered values: {update.message.text}\n')
            
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
            logger.info(f'User {update.effective_user.full_name} entered {context.user_data["finance_entry"]} = {update.message.text}')
            
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
    except:
        context.user_data['parent'] = SE_FINANCE
        
        await update.message.reply_text(
            '<b>Значение не соответствует формату, попробуй снова</b>',
            reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(_b_return, callback_data="return")]]), 
            parse_mode='HTML'
        )
        return SE_FINANCE

    await draw_finance_menu(update, context)

    return SE_FINANCE

async def finance_read_all(update: Update, context:ContextTypes) -> int: 
    """gets "заполнить все поля" callback.query && send explanational messasage how to reply"""

    query = update.callback_query
    await query.answer()

    context.user_data["parent_menu"] = SE_FINANCE
    context.user_data["finance_entry"] = query.data

    # можно динамический сформировать текст                 
    text = "<b>Введи значения в таком порядке, каждое в новой строке:</b> \n\n"
    text += "наличные (" + str(shift_report.finance.cash) + "₽) \n"
    text += "безнал (" + str(shift_report.finance.cards) + "₽) \n"
    text += "инкассация (" + str(shift_report.finance.incass) + "₽) \n"
    text += "кол-во чеков (" + str(shift_report.finance.reciepts) + "шт) \n\n"

    await query.edit_message_text(
        text,
        reply_markup= InlineKeyboardMarkup([[InlineKeyboardButton(_b_return, callback_data="return")]]), 
        parse_mode='HTML'
    )
    return SE_FINANCE

# Comment
async def comment_menu(update: Update, context: ContextTypes) -> int: 
    query = update.callback_query
    await query.answer()

    logger.info("User %s entered comments menu", query.from_user.full_name)

    context.user_data["parent_menu"] = SE_MENU

    text = "<b>Отправь комментарий о смене: </b> \n"
    if shift_report.is_comment:
        text += "\nТекущий комментарий:\n" + shift_report.comment

    await query.edit_message_text(
        text, 
        reply_markup= InlineKeyboardMarkup([[InlineKeyboardButton(_b_return, callback_data="return")]]),
        parse_mode='HTML'
    )
    return SE_COMMENT


async def read_comment(update: Update, context: ContextTypes) -> int:
    """reads comment from last user's message"""
    
    shift_report.comment = update.message.text
    shift_report.is_comment = True

    logger.info("User %s entered: %s\n", update.message.from_user.full_name, update.message.text)
    await draw_main_menu(update, context, edit=False)

    return SE_MENU

async def pre_writeoffs_menu(update: Update, context: ContextTypes) -> int:
    query = update.callback_query
    await query.answer()

    logger.info("User %s entered pre writeoffs menu", query.from_user.full_name)

    context.user_data["parent_menu"] = SE_MENU
    msg : str = ''

    #
    if shift_report._writeoffs.quantity() > 0:
        msg += '<b>У тебя уже есть заполненые списания:</b>\n'
        
        num = 1
        for w in shift_report._writeoffs.data:
            msg += f'{num}. {w.product} - {w.quantity} - {w.comment} \n'
            num = num + 1

        msg += '\nТы можешь добавить к ним новые, или перезаписать эти'
        kb = [
                [    InlineKeyboardButton('Добавить', callback_data='add'), 
                     InlineKeyboardButton('Перезаписать', callback_data='rewrite')
                ],
                [    InlineKeyboardButton(_b_return, callback_data = "return")]

        ]
        await draw_menu(msg, kb, update, context, edit = True)
        return SE_WRITEOFFS

    else: 
        await writeoffs_input_menu(update, context) 
    return SE_WRITEOFFS

async def writeoffs_set_rewrite(update: Update, context: ContextTypes) -> int:

    logger.info(f"User {update.effective_user.full_name} choose to rewrite writeoffs")
    query = update.callback_query
    await query.answer()

    shift_report._writeoffs._rewrite = True

    await writeoffs_input_menu(update, context)
    return SE_WRITEOFFS

async def writeoffs_set_append(update: Update, context: ContextTypes) -> int:
    query = update.callback_query
    await query.answer()

    logger.info(f"User {update.effective_user.full_name} choose to edit writeoffs")

    shift_report._writeoffs._rewrite = False
    await writeoffs_input_menu(update, context)
    return SE_WRITEOFFS


# Writeoffs
async def writeoffs_input_menu(update: Update, context: ContextTypes) -> int: 
    query = update.callback_query
    await query.answer()

    logger.info("User %s entered writeoffs menu", query.from_user.full_name)

    context.user_data["parent_menu"] = SE_MENU
    
    msg = "<b>Отправь списания за смену в формате:</b>\n\n"
    msg += "Продукт 1 - количество - комментарий\n"
    msg += "Продукт 2 - количество - комментарий\n\n"

    if shift_report.is_writeoffs:
        msg += "Текущие списания:\n"
        
        num = 1
        for w in shift_report._writeoffs.data:
            msg += f'{num}. {w.product} - {w.quantity} - {w.comment} \n'
            num = num + 1

    await query.edit_message_text(
        msg, 
        reply_markup= InlineKeyboardMarkup([[
            InlineKeyboardButton(_b_return, callback_data="return")
        ]]),
        parse_mode='HTML'
    )
    return SE_WRITEOFFS

async def read_writeoffs(update: Update, context: ContextTypes) -> int:
    """reads writeoffs from last user's message"""
    logger_msg = f"User {update.message.from_user.full_name} sent request to insert writeoffs:\n{update.message.text}"
    logger.info(logger_msg)

    shift_report.writeoffs = update.message.text
    bad_lines : str = ''

    temp = update.message.text.splitlines() 
    
    if shift_report._writeoffs._rewrite == True:
        await shift_report._writeoffs.set_to_zero()
        shift_report.is_writeoffs = False
    
    for entry in update.message.text.splitlines():
        if not await shift_report._writeoffs.append_str(entry):
            bad_lines += (entry + '\n')

    if shift_report._writeoffs.quantity() > 0:
        shift_report.is_writeoffs = True
    
    if not bad_lines == '' :
        logger_msg = f'Failed to insert writoffs:\n{bad_lines}' 
        logger.info(logger_msg)
        
        msg = '<b>Не получилось добавить эти строки</b>:\n'
        msg += bad_lines
        msg += '\nПроверь, соответствуют ли он формату, и повтори запрос'

        context.user_data['parent'] = SE_WRITEOFFS

        await draw_menu (
            msg,
            [[ InlineKeyboardButton('Окей', callback_data='ok')]],
            update,
            context,
            edit = False
        )
        return SE_WRITEOFFS

    logger_msg = f'Completed request' 
    logger.info(logger_msg)

    await draw_main_menu(update, context, edit=False)

    return SE_MENU

# Withdrawals

async def pre_withdrawals_menu(update: Update, context: ContextTypes) -> int:
    query = update.callback_query
    await query.answer()

    logger.info("User %s entered pre withdrawals menu", query.from_user.full_name)

    context.user_data["parent_menu"] = SE_MENU
    msg : str = ''

    #
    if shift_report._withdrawals.quantity() > 0:
        msg += '<b>У тебя уже есть заполненые изъятия</b>:\n\n'
        
        num = 1
        for w in shift_report._withdrawals.data:
            msg += f'{num}. {w.comment} - {w.sum}р \n'
            num = num + 1

        msg += '\nТы можешь добавить к ним новые, или перезаписать эти'
        kb = [
                [    InlineKeyboardButton('Добавить', callback_data='add'), 
                     InlineKeyboardButton('Перезаписать', callback_data='rewrite')
                ],
                [    InlineKeyboardButton(_b_return, callback_data = "return")]

        ]
        await draw_menu(msg, kb, update, context, edit = True)
        return SE_WITHDRAWALS

    else: 
        await withdrawals_input_menu(update, context) 
    return SE_WITHDRAWALS

async def withdrawals_set_rewrite(update: Update, context: ContextTypes) -> int:

    logger.info(f"User {update.effective_user.full_name} choose to rewrite withdarawals")
    query = update.callback_query
    await query.answer()

    shift_report._withdrawals._rewrite = True

    await withdrawals_input_menu(update, context)
    return SE_WITHDRAWALS

async def withdrawals_set_append(update: Update, context: ContextTypes) -> int:
    query = update.callback_query
    await query.answer()

    logger.info(f"User {update.effective_user.full_name} choose to edit withdarawals")

    shift_report._withdrawals._rewrite = False
    await withdrawals_input_menu(update, context)
    return SE_WITHDRAWALS

async def withdrawals_input_menu(update: Update, context: ContextTypes) -> int: 
    query = update.callback_query
    await query.answer()

    logger.info("User %s entered withdrawals input menu", query.from_user.full_name)

    context.user_data["parent_menu"] = SE_MENU

    msg = "<b>Отправь изьятия за смену в формате:</b>  \n\n"
    msg += "Поставщик 1 - Сумма\n"
    msg += "Поставщик 2 - Сумма\n\n"
    
    if shift_report.is_withdrawals:
        msg += "Текущие изъятия:\n"
        
        num = 1
        for w in shift_report._withdrawals.data:
            msg += f'{num}. {w.comment} - {w.sum}р \n'
            num = num + 1

    await query.edit_message_text(
        msg, 
        reply_markup= InlineKeyboardMarkup([[
            InlineKeyboardButton(_b_return, callback_data="return")
        ]]),
        parse_mode='HTML'
    )
    return SE_WITHDRAWALS

async def read_withdrawals(update: Update, context: ContextTypes) -> int:
    """reads withdrawals from last user's message"""
    logger_msg = f"User {update.message.from_user.full_name} sent request to insert withdrawals:\n{update.message.text}"
    logger.info(logger_msg)

    shift_report.withdrawals = update.message.text
    bad_lines : str = ''

    temp = update.message.text.splitlines() 
    
    if shift_report._withdrawals._rewrite == True:
        await shift_report._withdrawals.set_to_zero()
        shift_report.is_withdrawals = False
    
    for entry in update.message.text.splitlines():
        if not await shift_report._withdrawals.append_str(entry):
            bad_lines += (entry + '\n')

    if shift_report._withdrawals.quantity() > 0:
        shift_report.is_withdrawals = True
    
    if not bad_lines == '' :
        logger_msg = f'Failed to insert withdrawals:\n{bad_lines}' 
        logger.info(logger_msg)
        
        msg = '<b>Не получилось добавить эти строки</b>:\n'
        msg += bad_lines
        msg += '\nПроверь, соответствуют ли он формату, и повтори запрос'

        context.user_data['parent'] = SE_WITHDRAWALS

        await draw_menu (
            msg,
            [[ InlineKeyboardButton('Окей', callback_data='ok')]],
            update,
            context,
            edit = False
        )
        return SE_WITHDRAWALS

    logger_msg = f'Completed request' 
    logger.info(logger_msg)

    await draw_main_menu(update, context, edit=False)

    return SE_MENU

# Stoplist
async def stoplist_menu(update: Update, context: ContextTypes) -> int: 
    query = update.callback_query
    await query.answer()

    logger.info("User %s entered stop list menu", query.from_user.full_name)

    context.user_data['parent_menu'] = SE_MENU

    text = "<b>Заполни стоп лист в любом формате:</b>"

    if shift_report.is_stop_list:
        text += f"\n\nТекущий стоп лист:\n{str(shift_report.stop_list)}"
        # тут можно узнать у пользователя, хочет ли он добавить что то к текущей записи, или переписать 

    await query.edit_message_text(
        text, 
        reply_markup= InlineKeyboardMarkup([[InlineKeyboardButton(_b_return, callback_data="return")]]),
        parse_mode='HTML'
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
    
    text = "<b>Количество остатков:</b>\n\n"
    text += "Молоко: " + str(shift_report.leftovers.milk) + "л\n"
    text += "Эспрессо блэнд: " + str(shift_report.leftovers.espresso_blend) + "кг\n"

    _keyboard_leftovers = await _leftovers_keyboard()

    await query.edit_message_text(
        text,
        reply_markup = InlineKeyboardMarkup(_keyboard_leftovers), 
        parse_mode='HTML'
    )
    return SE_LEFTOVERS

async def draw_leftovers_menu (update: Update, context:ContextTypes) -> int: 
    """ Shows data values and send leftovers menu keyboard """    

    logger.info("Return to leftovers menu")
    logger.info("User %s entered leftovers report menu", update.message.from_user.full_name)

    context.user_data["parent_menu"] = SE_MENU   

    text = "<b>Количество остатков:</b> \n\n"
    text += "Молоко: " + str(shift_report.leftovers.milk) + "л\n"
    text += "Эспрессо блэнд: " + str(shift_report.leftovers.espresso_blend) + "кг\n"

    # parent const for return button navigation
    context.user_data ["parent_menu"] = SE_MENU

    leftovers = shift_report.leftovers

    _keyboard_leftovers = await _leftovers_keyboard()

    await update.message.reply_text(
        text,
        reply_markup = InlineKeyboardMarkup(_keyboard_leftovers), 
        parse_mode='HTML'
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
        "<b>Введи значение</b> : ",
        reply_markup= InlineKeyboardMarkup([[InlineKeyboardButton(_b_return, callback_data="return")]]), 
        parse_mode='HTML'
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

    text = "<b>Введи кто был на смене в формате: </b>\n Имя 1 - Часы\n Имя 2 - Часы\n"
    
    if shift_report.is_shift_team:
        text += "Текущая инфа: \n" + shift_report.shift_team

    await query.edit_message_text(
        text, 
        reply_markup
            = InlineKeyboardMarkup([[InlineKeyboardButton(_b_return, callback_data="return")]]),
        parse_mode='HTML'
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
async def message(update, context, text = "", silent = False, chat = 0):
    msg = await context.bot.send_message(chat_id= chat, text= text, parse_mode='HTML', disable_notification = silent, read_timeout = 15)
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
    #chat = config.SURF_X_MORE_TEST_CHAT

    # date and time    
    text = f"<b>Отчет по смене | Surf Coffee x {shift_report.spot_name}</b>"

    # date and time
    time_str = f'{datetime.today().time().hour}:{datetime.today().time().minute}'
    text += f'\n\n📅 {str(shift_report.date)}  🕒 {time_str}'
    
    await message(update, context, text = text, silent=True, chat=chat)

    text = ''
    # finance report
    text += "<b>Финансы: </b>\n\n"
    text += "💵 Наличные: " + num_to_str(shift_report.finance.cash) + " ₽\n"
    text += "💳 Карты: " + num_to_str(shift_report.finance.cards) + " ₽\n\n"
    
    text += "🧾 Чеки: " + num_to_str(shift_report.finance.reciepts) + "  "
    text += "🤑 Средний: " + num_to_str(shift_report.finance.medium_reciept()) + ' ₽\n\n'
    
    text += "💰 Инкассация: " + num_to_str(shift_report.finance.incass) + " ₽\n"
    text += "🪙 Размен: " + num_to_str(shift_report.finance.change) + " ₽\n"
    
    await message(update, context, text = text, silent=True, chat = chat)
    
    text = ''
    if (shift_report.finance.is_cash_returns):
        text += '🔙 Возвраты наличных: ' + num_to_str(shift_report.finance.cash_returns) + ' ₽\n'
        
    if (shift_report.finance.is_cards_returns):
        text += '🔙 Возвраты по картам: ' + num_to_str(shift_report.finance.cards_returns) + ' ₽\n'
    
    if (shift_report.finance.is_cash_returns == shift_report.finance.is_cash_returns == False):
        text += '🔙 Возвратов не было'
    
    await message(update, context, text = text, silent=True, chat = chat)

    # withdrawals data

    text = shift_report._withdrawals.to_report_text()
    
    #parse by lines and add tabs
    #lines = str(context.user_data["withdrawals"]).splitlines()
    #for line in lines: text += "    " + line + "\n"
    await message(update, context, text = text, silent=True, chat = chat)

    # writeoffs data
    text = shift_report._writeoffs.to_report_text()
    await message(update, context, text = text, silent=True, chat = chat)

    # leftovers data
    text = "<b>Остатки продуктов:</b>\n"
    text += "🥛 Молоко: " + num_to_str(shift_report.leftovers.milk) + " л\n"
    text += "🫘 Блэнд: " + num_to_str(shift_report.leftovers.espresso_blend) + " кг\n"
    await message(update, context, text = text, silent=True, chat = chat)
    
    # stop list data
    text = "<b>⛔ Стоп лист:</b>\n"
    for s in shift_report.stop_list.splitlines():
        text += '  ' + s + '\n'
    await message(update, context, text = text, silent=True, chat = chat)
    await message(update, context, text = text, silent=False, chat = config.SURF_X_MORE_MAIN_CHAT)

    # shift data
    text = "🏄‍♂️ <b>В смене отработали бариста:</b> \n"

    for s in shift_report.shift_team.splitlines():
        text += '  ' + s + ' часов\n'
    await message(update, context, text = text, silent=True, chat = chat)
    
    # comment
    text = "💬 <b>Комментарий:</b>\n"
    for s in shift_report.comment.splitlines():
        text += '  ' + s + '\n'
    await message(update, context, text = text, silent=True, chat = chat)

    context.user_data["parent_menu"] = SE_MENU
    

    # who sent report-user.full_name
    text = "\n🙋‍♂️ <b>Заполнил: </b> @" + update.effective_user.username
    
    await message(update, context, text = text, chat = chat)
    
    shift_report._is_sent = True
    #await shift_report_to_zero()    

    await query.edit_message_text(
        'Отчет успешно отправлен'
    )

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

    logger.info("User %s chose preview", query.from_user.full_name)
    
    text = f"<b>Отчет по смене | Surf Coffee x {shift_report.spot_name}</b>"

    # date and time
    time_str = f'{datetime.today().time().hour}:{datetime.today().time().minute}'
    text += f'\n\n📅 {str(shift_report.date)}  🕒 {time_str}'
    
    text += '\n\n'

    # finance report
    text += f'\n<b> Финансы: </b>\n\n'
    cash = num_to_str(shift_report.finance.cash)
    text += f'💵 Наличные: {cash} ₽\n'
    text += f"💳 Карты: {num_to_str(shift_report.finance.cards)} ₽\n\n"
    
    text += "🧾 Чеки: " + num_to_str(shift_report.finance.reciepts) + "  "
    text += "🤑 Средний: " + num_to_str(shift_report.finance.medium_reciept()) + ' ₽\n\n'
    
    text += "💰 Инкассация: " + num_to_str(shift_report.finance.incass) + " ₽\n"
    text += "🪙 Размен: " + num_to_str(shift_report.finance.change) + " ₽\n"
    
    if (shift_report.finance.is_cash_returns):
        text += '\n🔙 Возвраты наличных: ' + num_to_str(shift_report.finance.cash_returns) + ' ₽\n'
        
    if (shift_report.finance.is_cards_returns):
        text += '\n🔙 Возвраты по картам: ' + num_to_str(shift_report.finance.cards_returns) + ' ₽\n'
    
    # withdrawals data
    text += '\n\n'
    
    text += shift_report._withdrawals.to_report_text()
    text += '\n\n'

    # writeoffs data
    text += shift_report._writeoffs.to_report_text()
    text += '\n\n'  

    # leftovers data
    text += "<b>Остатки продуктов:</b>\n"
    text += "🥛 Молоко: " + num_to_str(shift_report.leftovers.milk) + " л\n"
    text += "🫘 Блэнд: " + num_to_str(shift_report.leftovers.espresso_blend) + " кг\n"
    text += '\n\n'
    
    # stop list data
    text += "<b>⛔ Стоп лист:</b>\n"
    for s in shift_report.stop_list.splitlines():
        text += '  ' + s + '\n'
    text += '\n'
    
    # shift data
    text += "🏄‍♂️ <b>В смене отработали бариста:</b> \n"

    for s in shift_report.shift_team.splitlines():
        text += '  ' + s + ' часов\n'
    text += '\n'
    
    # comment
    text += "💬 <b>Комментарий:</b>\n"
    for s in shift_report.comment.splitlines():
        text += '  ' + s + '\n'
    
    
    # who sent report-user.full_name
    text += "\n🙋‍♂️ <b>Заполнил: </b> @" + update.effective_user.username

    await query.answer()
    await query.edit_message_text(
        text, 
        reply_markup
            = InlineKeyboardMarkup([[
                InlineKeyboardButton("Отправить отчет", callback_data="send_report"),
                InlineKeyboardButton(_b_return, callback_data="return")]]),
        parse_mode='HTML'
    )


    return SE_PREVIEW

def num_to_str(x, digits : int = 1) -> str:
    if (type(x) == int):
        return str(x)
    elif (type(x) == str):
        return x
    elif (type(x) != float):
        return str(x)
    elif (x % 1 == 0): 
        return str(int(x))
    else:
        return str(round(x, digits))

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

    msg =  'Бот закрытия смены, который должен сделать твою жизнь чуть чуть проще\n\n'
    msg += 'Если нужна какая то помощь, или есть какой то фидбек, пиши сюды: @fruqube\n\n'
    msg += 'Проект еще в разработке, так что пользуйся осторожно\n'

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

    if parent == SE_WITHDRAWALS:
        await withdrawals_input_menu(update, context)

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
            CallbackQueryHandler(start_conversation_menu_from_query,  pattern = '^' + 'start_shift_end_from_start_button' + '$')
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
                CallbackQueryHandler(pre_writeoffs_menu, pattern = "^" + "writeoffs" + "$"),
                CallbackQueryHandler(pre_withdrawals_menu, pattern = "^" + "withdrawals" + "$"),
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
                CallbackQueryHandler(writeoffs_set_append, pattern="^" + "add" + "$"),
                CallbackQueryHandler(writeoffs_set_rewrite, pattern="^" + "rewrite" + "$"),
                CallbackQueryHandler(writeoffs_set_append, pattern="^" + "ok" + "$"),
                MessageHandler(filters.TEXT & (~filters.COMMAND), read_writeoffs)
            ],
            SE_WITHDRAWALS: [
                CallbackQueryHandler(withdrawals_set_append, pattern="^" + "add" + "$"),
                CallbackQueryHandler(withdrawals_set_rewrite, pattern="^" + "rewrite" + "$"),
                CallbackQueryHandler(withdrawals_set_append, pattern="^" + "ok" + "$"),
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

