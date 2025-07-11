import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS").split(",")))

    SEATABLE_API_URL = os.getenv("SEATABLE_API_URL")
    SEATABLE_API_TOKEN = os.getenv("SEATABLE_API_TOKEN")
    SEATABLE_EMAILS = os.getenv("SEATABLE_EMAILS")
    SEATABLE_GROUPS = os.getenv("SEATABLE_GROUPS")

    IMAP_SERVER = os.getenv("IMAP_SERVER")
    IMAP_EMAIL_SR01 = os.getenv("IMAP_EMAIL_SR01")
    IMAP_PASSWORD_SR01 = os.getenv("IMAP_PASSWORD_SR01")

    IMAP_EMAIL_SR02 = os.getenv("IMAP_EMAIL_SR02")
    IMAP_PASSWORD_SR02 = os.getenv("IMAP_PASSWORD_SR02")