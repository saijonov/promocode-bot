import xlsxwriter
from io import BytesIO
from datetime import datetime

async def export_users_to_excel(users):
    """Export users data to Excel file"""
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet("Foydalanuvchilar")
    
    # Add headers
    headers = ["№", "Telegram ID", "Ism", "Telefon raqami", "Ro'yxatdan o'tgan vaqt", "Promokodlar soni"]
    for col, header in enumerate(headers):
        worksheet.write(0, col, header)
    
    # Add data
    for row, user in enumerate(users, start=1):
        worksheet.write(row, 0, row)
        worksheet.write(row, 1, str(user['telegram_id']))
        worksheet.write(row, 2, user['full_name'])
        worksheet.write(row, 3, user['phone_number'])
        worksheet.write(row, 4, user['registered_at'].strftime('%Y-%m-%d %H:%M:%S'))
        worksheet.write(row, 5, user['promocode_count'])
    
    workbook.close()
    output.seek(0)
    return output

async def export_promocodes_to_excel(promocodes):
    """Export generated promocodes to Excel file"""
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet("Promokodlar")
    
    # Add headers
    headers = ["№", "Promokod"]
    for col, header in enumerate(headers):
        worksheet.write(0, col, header)
    
    # Add data
    for row, code in enumerate(promocodes, start=1):
        worksheet.write(row, 0, row)
        worksheet.write(row, 1, code)
    
    workbook.close()
    output.seek(0)
    return output

async def export_winners_to_excel(winners):
    """Export winners to Excel file"""
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet("G'oliblar")
    
    # Add headers
    headers = ["№", "Telegram ID", "Ism", "Telefon raqami", "Promokodlar soni"]
    for col, header in enumerate(headers):
        worksheet.write(0, col, header)
    
    # Add data
    for row, winner in enumerate(winners, start=1):
        worksheet.write(row, 0, row)
        worksheet.write(row, 1, str(winner['telegram_id']))
        worksheet.write(row, 2, winner['full_name'])
        worksheet.write(row, 3, winner['phone_number'])
        worksheet.write(row, 4, winner['promocode_count'])
    
    workbook.close()
    output.seek(0)
    return output