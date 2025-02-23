import flet as ft


async def main(page: ft.Page):
    page.title = "Nabu Voice Notes"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.update()


ft.app(target=main)
