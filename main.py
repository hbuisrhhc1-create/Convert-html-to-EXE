from threading import RLock

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

try:
    from android.permissions import request_permissions
    from jnius import PythonJavaClass, autoclass, java_method

    ON_ANDROID = True
except ImportError:
    ON_ANDROID = False


if ON_ANDROID:
    class BleScanCallback(PythonJavaClass):
        """Callback for nearby Bluetooth LE advertisements."""

        __javainterfaces__ = [
            'android/bluetooth/BluetoothAdapter$LeScanCallback'
        ]
        __javacontext__ = 'app'

        @java_method('(Landroid/bluetooth/BluetoothDevice;I[B)V')
        def onLeScan(self, device, rssi, scan_record):
            try:
                name = device.getName()
            except Exception:
                name = None

            if not name:
                name = 'מכשיר Bluetooth ללא שם'

            app = App.get_running_app()
            if app:
                Clock.schedule_once(
                    lambda _dt: app.add_signal(
                        'Bluetooth LE', str(name), int(rssi)
                    ),
                    0
                )


class WirelessRadarApp(App):
    SCAN_SECONDS = 25

    def build(self):
        self.title = 'גלאי אותות אלחוטיים'
        self.signals = {}
        self.lock = RLock()
        self.bluetooth_adapter = None
        self.ble_callback = None
        self.scanning = False
        self.wifi_event = None
        self.stop_event = None

        root = BoxLayout(
            orientation='vertical',
            padding=dp(16),
            spacing=dp(10)
        )

        self.status = Label(
            text='לחצו על הכפתור כדי לבקש הרשאות ולהתחיל סריקה.',
            size_hint_y=None,
            height=dp(58),
            halign='right',
            valign='middle'
        )
        self.status.bind(size=self._fit_label)
        root.add_widget(self.status)

        self.scan_button = Button(
            text='בקש הרשאות והתחל סריקה',
            size_hint_y=None,
            height=dp(54)
        )
        self.scan_button.bind(on_release=self.on_scan_button)
        root.add_widget(self.scan_button)

        note = Label(
            text=(
                'Wi‑Fi מציג רשתות שנקלטות, לא מכשירים המחוברים אליהן. '
                'עוצמת האות אינה מדידת מרחק.'
            ),
            size_hint_y=None,
            height=dp(62),
            halign='right',
            valign='middle'
        )
        note.bind(size=self._fit_label)
        root.add_widget(note)

        self.results = Label(
            text='עדיין אין תוצאות.',
            size_hint_y=None,
            halign='right',
            valign='top'
        )
        self.results.bind(
            texture_size=lambda label, size: setattr(
                label, 'height', size[1] + dp(20)
            )
        )

        scroll = ScrollView()
        scroll.add_widget(self.results)
        root.add_widget(scroll)

        if not ON_ANDROID:
            self.status.text = (
                'האפליקציה הזו מיועדת ל-Android ויש לארוז אותה כ-APK.'
            )
            self.scan_button.disabled = True

        return root

    @staticmethod
    def _fit_label(label, _size):
        label.text_size = (label.width - dp(12), None)

    def on_scan_button(self, *_args):
        if not ON_ANDROID:
            return

        if self.scanning:
            self.stop_scanning()
            return

        try:
            version = autoclass('android.os.Build$VERSION')
            sdk = int(version.SDK_INT)
        except Exception:
            sdk = 30

        permissions = [
            'android.permission.ACCESS_FINE_LOCATION',
            'android.permission.ACCESS_COARSE_LOCATION',
            'android.permission.ACCESS_WIFI_STATE',
            'android.permission.CHANGE_WIFI_STATE',
        ]

        if sdk >= 31:
            permissions.extend([
                'android.permission.BLUETOOTH_SCAN',
                'android.permission.BLUETOOTH_CONNECT',
            ])
        else:
            permissions.extend([
                'android.permission.BLUETOOTH',
                'android.permission.BLUETOOTH_ADMIN',
            ])

        if sdk >= 33:
            permissions.append('android.permission.NEARBY_WIFI_DEVICES')

        self.status.text = 'מבקש הרשאות Android...'

        try:
            request_permissions(permissions, self.on_permissions_result)
        except Exception as exc:
            self.status.text = f'לא ניתן לבקש הרשאות: {exc}'

    def on_permissions_result(self, _permissions, grant_results):
        # Buildozer reports each permission grant as a boolean.
        if not grant_results or not all(bool(value) for value in grant_results):
            Clock.schedule_once(
                lambda _dt: setattr(
                    self.status,
                    'text',
                    'לא כל ההרשאות אושרו. אפשר לנסות שוב ולאשר את הבקשות.'
                ),
                0
            )
            return

        Clock.schedule_once(lambda _dt: self.start_scanning(), 0)

    def start_scanning(self):
        if self.scanning:
            return

        self.scanning = True
        self.signals.clear()
        self.refresh_results()
        self.scan_button.text = 'עצור סריקה'
        self.status.text = f'סורק במשך עד {self.SCAN_SECONDS} שניות...'

        self.start_ble_scan()
        self.refresh_wifi()

        self.wifi_event = Clock.schedule_interval(self.refresh_wifi, 12)
        self.stop_event = Clock.schedule_once(
            self.finish_scanning, self.SCAN_SECONDS
        )

    def start_ble_scan(self):
        try:
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Context = autoclass('android.content.Context')

            activity = PythonActivity.mActivity
            manager = activity.getSystemService(Context.BLUETOOTH_SERVICE)

            if manager is None:
                self.status.text = 'שירות Bluetooth אינו זמין במכשיר.'
                return

            self.bluetooth_adapter = manager.getAdapter()

            if self.bluetooth_adapter is None:
                self.status.text = 'מתאם Bluetooth אינו זמין במכשיר.'
                return

            if not self.bluetooth_adapter.isEnabled():
                self.status.text = (
                    'Bluetooth כבוי. יש להפעיל אותו ולאחר מכן לנסות שוב.'
                )
                return

            self.ble_callback = BleScanCallback()
            started = self.bluetooth_adapter.startLeScan(self.ble_callback)

            if not started:
                self.status.text = 'Android לא התחיל סריקת Bluetooth LE.'

        except Exception as exc:
            self.status.text = f'שגיאה בסריקת Bluetooth: {exc}'

    def refresh_wifi(self, *_args):
        if not ON_ANDROID or not self.scanning:
            return

        try:
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Context = autoclass('android.content.Context')

            activity = PythonActivity.mActivity
            wifi = activity.getApplicationContext().getSystemService(
                Context.WIFI_SERVICE
            )

            if wifi is None:
                self.status.text = 'שירות Wi‑Fi אינו זמין במכשיר.'
                return

            if not wifi.isWifiEnabled():
                self.status.text = 'Wi‑Fi כבוי. יש להפעיל אותו ולנסות שוב.'
                return

            # Android may throttle scans; it can return cached results.
            wifi.startScan()
            Clock.schedule_once(
                lambda _dt: self.read_wifi_results(wifi),
                2
            )

        except Exception as exc:
            self.status.text = f'שגיאה בסריקת Wi‑Fi: {exc}'

    def read_wifi_results(self, wifi):
        if not self.scanning:
            return

        try:
            for result in wifi.getScanResults():
                ssid = str(result.SSID or '').strip()

                if not ssid or ssid == '<unknown ssid>':
                    ssid = 'רשת Wi‑Fi מוסתרת'

                self.add_signal('נקודת גישה Wi‑Fi', ssid, int(result.level))

        except Exception as exc:
            self.status.text = f'לא ניתן לקרוא תוצאות Wi‑Fi: {exc}'

    def add_signal(self, signal_type, name, rssi):
        key = (signal_type, name)

        with self.lock:
            self.signals[key] = {
                'type': signal_type,
                'name': name,
                'rssi': rssi,
            }

        self.refresh_results()

    def refresh_results(self):
        with self.lock:
            items = sorted(
                self.signals.values(),
                key=lambda item: item['rssi'],
                reverse=True
            )

        if not items:
            self.results.text = 'מחפש אותות...'
            return

        lines = []
        for item in items:
            rssi = item['rssi']
            bars_count = max(1, min(5, int((rssi + 100) / 12)))
            bars = '▮' * bars_count + '▯' * (5 - bars_count)

            lines.append(
                f"{item['type']}\n"
                f"{item['name']}\n"
                f"עוצמת קליטה משוערת: {rssi} dBm  {bars}\n"
            )

        self.results.text = '\n'.join(lines)

    def finish_scanning(self, _dt):
        self.stop_scanning()
        self.status.text = (
            f'הסריקה הסתיימה. נמצאו {len(self.signals)} אותות. '
            'ייתכן ש-Android הגביל את סריקות ה-Wi‑Fi.'
        )

    def stop_scanning(self):
        self.scanning = False
        self.scan_button.text = 'בקש הרשאות והתחל סריקה'

        if self.wifi_event is not None:
            self.wifi_event.cancel()
            self.wifi_event = None

        if self.stop_event is not None:
            self.stop_event.cancel()
            self.stop_event = None

        try:
            if self.bluetooth_adapter and self.ble_callback:
                self.bluetooth_adapter.stopLeScan(self.ble_callback)
        except Exception:
            pass

        self.bluetooth_adapter = None
        self.ble_callback = None

    def on_pause(self):
        self.stop_scanning()
        return True

    def on_stop(self):
        self.stop_scanning()


if __name__ == '__main__':
    WirelessRadarApp().run()
