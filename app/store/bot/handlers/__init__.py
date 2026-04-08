from aiogram import Dispatcher

def setup_routers(dp: Dispatcher):
    from .start import router as start_router
    from .form import router as form_router
    
    dp.include_router(start_router)
    dp.include_router(form_router)