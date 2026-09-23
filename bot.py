import os
from dotenv import load_dotenv

from telegram import ReplyKeyboardMarkup

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

from database import (
    init_db,
    create_user,
    get_user_by_code,
    get_user_code,
    get_user_name,
    get_username,
    create_conversation,
    get_conversation,
    close_conversation,
    add_block,
    is_blocked,
    create_message,
    get_message,
    mark_message_seen,
    clear_blocks,
    get_block_count
)

import secrets


# =====================================
# ACTIVE CHATS
# =====================================

active_chats = {}

    

# =====================================
# NEW MESSAGE BUTTON
# =====================================

async def send_my_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    code = get_user_code(user.id)

    if not code:
        code = secrets.token_urlsafe(8)

        create_user(
            user.id,
            code,
            user.first_name,
            user.username
        )

    bot_username = context.bot.username

    link = f"https://t.me/{bot_username}?start={code}"

    await update.message.reply_text(
        "🔗 لینک پیام ناشناس شما:\n\n"
        f"{link}\n\n"
        "این لینک را برای دیگران بفرستید تا بتوانند به صورت ناشناس برای شما پیام بفرستند."
    )

def message_keyboard(message_id):

    keyboard = [
        [
            InlineKeyboardButton(
                "🆕 New message",
                callback_data=f"newmsg:{message_id}"
            )
        ]
    ]

    return InlineKeyboardMarkup(keyboard)


# =====================================
# REPLY / BLOCK BUTTONS
# =====================================

def response_keyboard(conversation_id):

    keyboard = [
        [
            InlineKeyboardButton(
                "💬 پاسخ",
                callback_data=f"reply:{conversation_id}"
            ),
            InlineKeyboardButton(
                "🚫 بلاک",
                callback_data=f"block:{conversation_id}"
            )
        ]
    ]

    return InlineKeyboardMarkup(keyboard)


# =====================================
# START
# =====================================

def main_menu():

    keyboard = [
        ["🔗 لینک من", "⚙️ تنظیمات"],
        ["🚫 مدیریت بلاک‌ها", "ℹ️ درباره بات"],
        ["🔄 ری‌استارت"]
    ]

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    # ---------------------------------
    # OPENING AN ANONYMOUS LINK
    # ---------------------------------

    if context.args:

        anonymous_code = context.args[0]

        receiver_id = get_user_by_code(
            anonymous_code
        )

        if receiver_id is None:

            await update.message.reply_text(
                "❌ این لینک معتبر نیست."
            )

            return

        if receiver_id == user.id:

            await update.message.reply_text(
                "❌ نمی‌تونی به خودت پیام ناشناس بفرستی."
            )

            return

        if is_blocked(
            receiver_id,
            user.id
        ):

            await update.message.reply_text(
                "❌ امکان ارسال پیام به این کاربر وجود ندارد."
            )

            return

        # Create sender account if necessary
        sender_code = get_user_code(user.id)

        if sender_code is None:

            sender_code = secrets.token_urlsafe(8)

            create_user(
                user.id,
                sender_code,
                user.first_name or "کاربر",
                user.username
            )

        # Create conversation
        conversation_id = create_conversation(
            user.id,
            receiver_id
        )

        active_chats[user.id] = conversation_id

        receiver_name = get_user_name(
            receiver_id
        )

        await update.message.reply_text(
            f"👤 شما در حال ارسال پیام ناشناس به «{receiver_name}» هستید.\n\n"
            "هویت شما برای طرف مقابل نمایش داده نمی‌شود.\n\n"
            "پیامت رو بفرست 👇"
            
        )

        return

    # ---------------------------------
    # NORMAL START
    # ---------------------------------

    anonymous_code = get_user_code(
        user.id
    )

    if anonymous_code is None:

        anonymous_code = secrets.token_urlsafe(8)

        create_user(
            user.id,
            anonymous_code,
            user.first_name or "کاربر",
            user.username
        )

    bot_username = context.bot.username

    link = (
        f"https://t.me/"
        f"{bot_username}"
        f"?start={anonymous_code}"
    )

    await update.message.reply_text(
        "سلام 👋\n\n"
        "لینک اختصاصی دریافت پیام ناشناس تو:\n\n"
        f"{link}\n\n"
        "این لینک رو برای بقیه بفرست.",
        reply_markup=main_menu()
    )


# =====================================
# HANDLE INCOMING MESSAGE
# =====================================

async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    sender = update.effective_user
    text = update.message.text

    if text == "🔗 لینک من":

        await send_my_link(update, context)
        return

    if text == "ℹ️ درباره بات":

        await update.message.reply_text(
            "📩 Anonymous Bot\n\n"
            "نسخه: 1.0"
        )

        return

    if text == "⚙️ تنظیمات":

        await update.message.reply_text(
            "⚙️ این بخش در آینده تکمیل می‌شود."
        )

        return

    if text == "🔄 ری‌استارت":

        
        active_chats.pop(
            sender.id,
            None
        )

        
        await update.message.reply_text(
        "🔄 وضعیت شما ریست شد."
        )

        return

    if text == "🚫 مدیریت بلاک‌ها":

        count = get_block_count(sender.id)

        if count == 0:
            await update.message.reply_text(
                "🚫 شما در حال حاضر هیچ کاربری را بلاک نکرده‌اید."
            )
            return

        keyboard = [
            ["🔓 آزاد کردن همه بلاک‌ها"]
        ]

        await update.message.reply_text(
            f"🚫 تعداد کاربران بلاک‌شده: {count}\n\n"
            "می‌توانید همه‌ی بلاک‌ها را آزاد کنید.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )

        return

    if text == "🔓 آزاد کردن همه بلاک‌ها":

        clear_blocks(sender.id)

        await update.message.reply_text(
            "🔓 همه‌ی کاربران بلاک‌شده آزاد شدند.",
            reply_markup=main_menu()
        )

        return
        

    conversation_id = active_chats.get(
        sender.id
    )

    if conversation_id is None:

        await update.message.reply_text(
            "⚠️ ابتدا از طریق لینک ناشناس یک نفر وارد مکالمه شو."
        )

        return

    conversation = get_conversation(
        conversation_id
    )

    if conversation is None:

        active_chats.pop(
            sender.id,
            None
        )

        await update.message.reply_text(
            "❌ این مکالمه وجود ندارد."
        )

        return

    (
        _,
        user_a,
        user_b,
        status
    ) = conversation

    if status != "active":

        active_chats.pop(
            sender.id,
            None
        )

        await update.message.reply_text(
            "🔴 این مکالمه بسته شده."
        )

        return

    # Find receiver
    if sender.id == user_a:

        receiver_id = user_b

    elif sender.id == user_b:

        receiver_id = user_a

    else:

        await update.message.reply_text(
            "❌ شما عضو این مکالمه نیستید."
        )

        return

    # Check block
    if is_blocked(
        receiver_id,
        sender.id
    ):

        await update.message.reply_text(
            "🚫 این کاربر شما را مسدود کرده است."
        )

        active_chats.pop(
            sender.id,
            None
        )

        return

    # =================================
    # DETECT MESSAGE TYPE
    # =================================

    message_type = None
    message_text = None
    file_id = None
    caption = None

    # TEXT
    if update.message.text:

        message_type = "text"

        message_text = update.message.text

    # VOICE
    elif update.message.voice:

        message_type = "voice"

        file_id = update.message.voice.file_id

        caption = update.message.caption

    # PHOTO
    elif update.message.photo:

        message_type = "photo"

        # Telegram provides multiple resolutions.
        # We use the largest one.
        file_id = update.message.photo[-1].file_id

        caption = update.message.caption

    # VIDEO
    elif update.message.video:

        message_type = "video"

        file_id = update.message.video.file_id

        caption = update.message.caption

    else:

        await update.message.reply_text(
            "⚠️ فعلاً فقط متن، عکس، ویس و ویدئو پشتیبانی می‌شود."
        )

        return

    # =================================
    # SAVE MESSAGE
    # =================================

    message_id = create_message(
        conversation_id=conversation_id,
        sender_id=sender.id,
        receiver_id=receiver_id,
        message_type=message_type,
        message_text=message_text,
        file_id=file_id,
        caption=caption
    )

    # =================================
    # SEND NEW MESSAGE NOTIFICATION
    # =================================

    await context.bot.send_message(
        chat_id=receiver_id,
        text=(
            "📩 پیام جدید دارید!\n\n"
            "برای مشاهده پیام روی دکمه زیر بزنید."
        ),
        reply_markup=message_keyboard(
            message_id
        )
    )

    await update.message.reply_text(
        "✅ پیام ارسال شد.\n\n"
        "وقتی طرف مقابل پیامت رو باز کنه، بهت اطلاع می‌دیم."
    )


# =====================================
# CALLBACK HANDLER
# =====================================

async def callback_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    data = query.data

    # =================================
    # NEW MESSAGE
    # =================================

    if data.startswith("newmsg:"):

        message_id = data.split(
            ":",
            1
        )[1]

        message = get_message(
            message_id
        )

        if message is None:

            await query.message.reply_text(
                "❌ این پیام دیگر وجود ندارد."
            )

            return

        (
            message_id,
            conversation_id,
            sender_id,
            receiver_id,
            message_type,
            message_text,
            file_id,
            caption,
            status
        ) = message

        # Security
        if query.from_user.id != receiver_id:

            await query.message.reply_text(
                "❌ این پیام برای شما نیست."
            )

            return

        if status == "seen":

            await query.message.reply_text(
                "⚠️ این پیام قبلاً دیده شده."
            )

            return

        # =================================
        # MARK AS SEEN
        # =================================

        mark_message_seen(
            message_id
        )

        # =================================
        # SHOW MESSAGE
        # =================================

        if message_type == "text":

            await query.message.reply_text(
                "📩 پیام ناشناس:\n\n"
                f"{message_text}",
                reply_markup=response_keyboard(
                    conversation_id
                )
            )

        elif message_type == "voice":

            await query.message.reply_text(
                "📩 پیام ناشناس:"
            )

            await context.bot.send_voice(
                chat_id=receiver_id,
                voice=file_id,
                caption=caption,
                reply_markup=response_keyboard(
                    conversation_id
                )
            )

        elif message_type == "photo":

            await context.bot.send_photo(
                chat_id=receiver_id,
                photo=file_id,
                caption=(
                    f"📩 پیام ناشناس:\n\n{caption}"
                    if caption
                    else "📩 پیام ناشناس"
                ),
                reply_markup=response_keyboard(
                    conversation_id
                )
            )

        elif message_type == "video":

            await context.bot.send_video(
                chat_id=receiver_id,
                video=file_id,
                caption=(
                    f"📩 پیام ناشناس:\n\n{caption}"
                    if caption
                    else "📩 پیام ناشناس"
                ),
                reply_markup=response_keyboard(
                    conversation_id
                )
            )

        # =================================
        # TELL SENDER
        # =================================

        await context.bot.send_message(
            chat_id=sender_id,
            text="👁️ پیامت دیده شد."
        )

        return

    # =================================
    # REPLY
    # =================================

    if data.startswith("reply:"):

        conversation_id = data.split(
            ":",
            1
        )[1]

        conversation = get_conversation(
            conversation_id
        )

        if conversation is None:

            await query.message.reply_text(
                "❌ این مکالمه وجود ندارد."
            )

            return

        (
            _,
            user_a,
            user_b,
            status
        ) = conversation

        user_id = query.from_user.id

        if user_id not in (
            user_a,
            user_b
        ):

            await query.message.reply_text(
                "❌ شما عضو این مکالمه نیستید."
            )

            return

        if status != "active":

            await query.message.reply_text(
                "🔴 این مکالمه بسته شده."
            )

            return

        active_chats[user_id] = conversation_id

        await query.message.reply_text(
            "💬 مکالمه فعال شد.\n\n"
            "متن، عکس، ویس یا ویدئوت رو بفرست 👇"
        )

        return

    # =================================
    # BLOCK
    # =================================

    if data.startswith("block:"):

        conversation_id = data.split(
            ":",
            1
        )[1]

        conversation = get_conversation(
            conversation_id
        )

        if conversation is None:
            return

        (
            _,
            user_a,
            user_b,
            status
        ) = conversation

        user_id = query.from_user.id

        if user_id not in (
            user_a,
            user_b
        ):
            return

        other_user = (
            user_b
            if user_id == user_a
            else user_a
        )

        add_block(
            user_id,
            other_user
        )

        close_conversation(
            conversation_id
        )

        active_chats.pop(
            user_a,
            None
        )

        active_chats.pop(
            user_b,
            None
        )

        await query.message.reply_text(
            "🚫 کاربر مسدود شد و مکالمه پایان یافت."
        )

        await context.bot.send_message(
            chat_id=other_user,
            text=(
                "🚫 امکان ادامه این مکالمه "
                "وجود ندارد."
            )
        )

        return

def clear_blocks(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM blocks
        WHERE blocker_id = ?
        """,
        (user_id,)
    )

    conn.commit()
    conn.close()

def get_block_count(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM blocks
        WHERE blocker_id = ?
        """,
        (user_id,)
    )

    count = cursor.fetchone()[0]

    conn.close()

    return count


# =====================================
# MAIN
# =====================================

def main():

    init_db()
    
    load_dotenv()
    
    TOKEN = os.getenv("BOT_TOKEN")
    
    print("BOT_TOKEN exists:", bool(TOKEN))
    
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN is not set")

    application = (
        Application
        .builder()
        .token(TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            callback_handler
        )
    )

    # Text / Voice / Photo / Video
    application.add_handler(
        MessageHandler(
            (
                filters.TEXT
                | filters.VOICE
                | filters.PHOTO
                | filters.VIDEO
            )
            & ~filters.COMMAND,
            handle_message
        )
    )

    print("Bot is running...")

    application.run_polling()


if __name__ == "__main__":
    main()

