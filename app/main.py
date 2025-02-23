import asyncio
import datetime
import flet as ft


def main(page: ft.Page):
    page.title = "Nabu Voice Notes"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    recorder = ft.AudioRecorder(ft.AudioEncoder.WAV)
    page.overlay.append(recorder)

    def route_change(route: str):
        page.views.clear()

        page.views.append(main_view(page))

        if page.route == "/settings":
            page.views.append(settings_view(page))

        if page.route == "/new":
            page.views.append(new_note_view(page, recorder))

        page.update()

    def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop

    page.go(page.route)


def main_view(page: ft.Page) -> ft.View:
    view = ft.View(
        "/",
        [
            ft.Row(
                [
                    ft.Text("Notes"),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            )
        ],
    )

    view.appbar = ft.AppBar(
        title=ft.Text(
            "Nabu Voice Notes", weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK87
        ),
        actions=[
            ft.IconButton(
                ft.Icons.SETTINGS,
                tooltip="Settings",
                icon_color=ft.Colors.BLACK87,
                on_click=lambda _: page.go("/settings"),
            )
        ],
        bgcolor=ft.Colors.BLUE,
        center_title=True,
        color=ft.Colors.WHITE,
    )

    view.floating_action_button = ft.FloatingActionButton(
        icon=ft.Icons.MIC, scale=1.5, bgcolor=ft.Colors.RED_600, on_click=lambda _: page.go("/new")
    )

    return view


def settings_view(page: ft.Page) -> ft.View:
    view = ft.View("/settings", [ft.Text("Profile")])

    view.appbar = ft.AppBar(
        title=ft.Text("Settings", weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK87),
        bgcolor=ft.Colors.BLUE,
        center_title=True,
        color=ft.Colors.WHITE,
    )

    return view


class Timer(ft.Text):
    def __init__(self):
        super().__init__()
        self.value = "00:00:00"
        self.timer = 0
        self.running = False

    def resume(self):
        self.running = True

    def pause(self):
        self.running = False

    def did_mount(self):
        self.page.run_task(self.run)

    def will_unmount(self):
        self.running = False

    async def run(self):
        while True:
            if self.running:
                self.timer += 1
                self.value = str(datetime.timedelta(seconds=self.timer))
                await asyncio.sleep(1)
                self.update()


def new_note_view(page: ft.Page, recorder: ft.AudioRecorder) -> ft.View:
    status_control = ft.Text("Status: recording")
    duration_control = Timer()

    # mic_button = ft.IconButton(icon=ft.Icons.PAUSE, bgcolor=ft.Colors.RED_700)

    done_button = ft.IconButton(
        icon=ft.Icons.STOP,
        bgcolor=ft.Colors.GREEN_600,
    )

    recorder.start_recording("sample.wav")
    duration_control.resume()

    # def resume_recording():
    #     recorder.resume_recording()
    #     status_control.value = "Status: recording"
    #     mic_button.icon = ft.Icons.PAUSE
    #     duration_control.resume()
    #     page.update()

    # def pause_recording():
    #     recorder.pause_recording()
    #     status_control.value = "Status: paused"
    #     mic_button.icon = ft.Icons.MIC
    #     duration_control.pause()
    #     page.update()

    def done(e):
        done_button.disabled = True
        done_button.update()
        duration_control.pause()
        result = recorder.stop_recording()
        print("RECORDING", result)
        status_control.value = "Status: processing...."
        page.update()

    done_button.on_click = done

    # def on_mic_click(e):
    #     if recorder.is_paused():
    #         resume_recording()
    #     else:
    #         pause_recording()

    # mic_button.on_click = on_mic_click

    view = ft.View(
        "/new",
        [
            ft.Text(
                "We are live! You can start talking now. When done, press the green button. To cancel (and discard the note!) press the back button in the top navbar."
            ),
            status_control,
            duration_control,
            ft.Row(
                [
                    # mic_button,
                    done_button,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                scale=1.8,
                expand=True,
            ),
        ],
        vertical_alignment=ft.VerticalAlignment.CENTER,
    )

    view.appbar = ft.AppBar(
        title=ft.Text("New Note", weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK87),
        bgcolor=ft.Colors.BLUE,
        center_title=True,
        color=ft.Colors.WHITE,
    )

    return view


ft.app(target=main)
