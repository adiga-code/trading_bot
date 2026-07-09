from aiogram import Router

from app.bot.routers import admin, menu, pay, shop, start


def build_root_router() -> Router:
    root = Router()
    # admin первым: его FSM-состояния перехватывают текст раньше общих хендлеров
    root.include_router(admin.router)
    root.include_router(start.router)
    root.include_router(shop.router)
    root.include_router(pay.router)
    root.include_router(menu.router)
    return root
