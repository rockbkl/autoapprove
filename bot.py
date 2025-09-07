import json
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import asyncio

# ================== CONFIG ==================
api_id = 28593100
api_hash = "5e5683849a39c73f87ec02ebba4561b4"
bot_token = "7311482488:AAGT2Yd6VQOFgMIIfIhU7u9zPBrDhrGi2Y8"
OWNER_ID = 7942764517   # tumhara Telegram ID
USERS_FILE = "users.json"
# ============================================

# save users for broadcast
def save_user(user_id):
    try:
        with open(USERS_FILE, "r") as f:
            users = json.load(f)
    except:
        users = []

    if user_id not in users:
        users.append(user_id)
        with open(USERS_FILE, "w") as f:
            json.dump(users, f)

# load all users
def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except:
        return []

app = Client("AutoApprovedBot", bot_token=bot_token, api_id=api_id, api_hash=api_hash)

# Start command
@app.on_message(filters.private & filters.command("start"))
async def start(client, message: Message):
    me = await client.get_me()
    button = [[InlineKeyboardButton("➕ Add Me To Channel/Group", url=f"http://t.me/{me.username}?startgroup=botstart")]]
    await message.reply_text(
        f"👋 Hello {message.from_user.mention}, I am **Auto Approve Bot**!\n\n"
        "✅ Add me as **Admin** in your channel/group (with Add Members permission).\n"
        "✅ I will automatically approve join requests.\n"
        "✅ Use /approveall in group/channel to approve pending requests.\n"
        "✅ Owner can use /broadcast to message all users.",
        reply_markup=InlineKeyboardMarkup(button),
        disable_web_page_preview=True
    )
    save_user(message.from_user.id)

# Bulk approve command (works in group + supergroup + channel)
@app.on_message(filters.command("approveall") & (filters.group | filters.supergroup | filters.channel))
async def approve_all(client, message: Message):
    chat = message.chat

    # Check if bot is admin
    bot_info = await client.get_chat_member(chat.id, "me")
    if not bot_info.privileges or not bot_info.privileges.can_invite_users:
        await message.reply_text("❌ I need to be an admin with 'Add Members' permission to approve requests!")
        return

    # Check if command user is admin (only for groups/supergroups)
    if chat.type in ["group", "supergroup"]:
        user_info = await client.get_chat_member(chat.id, message.from_user.id)
        if user_info.status not in ["creator", "administrator"]:
            await message.reply_text("❌ You need to be an admin to use this command!")
            return

    processing_msg = await message.reply_text("⏳ Processing pending join requests...")

    try:
        reqs = []
        async for req in client.get_chat_join_requests(chat.id):
            reqs.append(req)

        if not reqs:
            await processing_msg.edit_text("🙂 No pending join requests found.")
            return

        approved = 0
        for user in reqs:
            try:
                await client.approve_chat_join_request(chat.id, user.from_user.id)
                if not user.from_user.is_bot:
                    try:
                        await client.send_message(
                            user.from_user.id,
                            f"👋 Hello {user.from_user.mention},\n\n"
                            f"✅ Your request has been accepted!\n"
                            f"🎉 Approved by **AutoApprove Bot** in: {chat.title}"
                        )
                        save_user(user.from_user.id)
                    except:
                        pass
                approved += 1
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"Error approving {user.from_user.id}: {e}")
                continue

        await processing_msg.edit_text(f"✅ Approved **{approved}** members successfully in **{chat.title}**!")
    except Exception as e:
        await processing_msg.edit_text(f"❌ Error: {str(e)}")

# Auto approve join requests
@app.on_chat_join_request(filters.group | filters.channel)
async def autoapprove(client, request):
    chat = request.chat
    user = request.from_user

    try:
        await client.approve_chat_join_request(chat.id, user.id)
        print(f"✅ {user.first_name} auto-approved in {chat.title}")
        
        if not user.is_bot:
            try:
                await client.send_message(
                    user.id,
                    f"👋 Hello {user.mention},\n\n"
                    f"✅ Your request has been accepted!\n"
                    f"🎉 Approved by **AutoApprove Bot** in: {chat.title}"
                )
                save_user(user.id)
            except:
                pass
    except Exception as e:
        print(f"❌ Error: {e}")

# Broadcast command (Owner only)
@app.on_message(filters.private & filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast(client, message: Message):
    if len(message.text.split()) < 2:
        await message.reply_text("⚠️ Usage: `/broadcast your_message_here`", quote=True)
        return

    text = message.text.split(" ", 1)[1]
    users = load_users()
    total = len(users)
    success = 0
    fail = 0
    
    processing_msg = await message.reply_text(f"📢 Broadcasting to {total} users...")

    for uid in users:
        try:
            await client.send_message(uid, text)
            success += 1
            if success % 10 == 0:
                await processing_msg.edit_text(
                    f"📢 Broadcasting...\n"
                    f"✅ Success: {success}\n"
                    f"❌ Failed: {fail}\n"
                    f"📊 Total: {total}"
                )
            await asyncio.sleep(0.1)
        except:
            fail += 1

    await processing_msg.edit_text(
        f"📢 **Broadcast Summary**\n\n"
        f"👥 Total Users: {total}\n"
        f"✅ Success: {success}\n"
        f"❌ Failed: {fail}"
    )

if __name__ == "__main__":
    print("🚀 Auto Approve Bot with Broadcast started...")
    app.run()
