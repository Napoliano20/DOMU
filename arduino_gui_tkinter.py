#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
import tkinter as tk
from tkinter import ttk, messagebox
import serial
import serial.tools.list_ports
import threading
import subprocess  # Cheese kamera uygulamasını başlatmak için
import datetime    # Tarih bilgisi için
import random      # Manuel hava durumu için rastgele değerler

class ArduinoControlGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("DOMU - Ev Otomasyonu Kontrol Paneli")
        self.root.geometry("960x680")  # Pencere boyutunu büyüttük
        self.root.resizable(True, True)  # Pencere yeniden boyutlandırılabilir
        
        # Uygulama değişkenleri
        self.serial_port = None
        self.led_status = [False, False, False, False]
        self.pot_value = tk.IntVar(value=0)
        self.connected = False
        self.reading_thread = None
        self.stop_thread = False
        self.visitor_count = 0  # Ziyaretçi sayacı
        self.door_open = False  # Kapı durumu (açık/kapalı)
        self.auto_update_temp = False  # Otomatik sıcaklık güncelleme
        self.auto_update_job = None  # Zamanlayıcı işi
        
        # Hava durumu ve tarih değişkenleri
        self.current_date = datetime.datetime.now().strftime("%d.%m.%Y")
        self.current_time = tk.StringVar(value=datetime.datetime.now().strftime("%H:%M:%S"))
        self.temperature = tk.StringVar(value="-- °C")
        self.weather_condition = tk.StringVar(value="Bilinmiyor")
        self.weather_update_time = tk.StringVar(value="--:--")

        # Stil ayarları
        style = ttk.Style()
        
        # Tema renkleri - Açık Tema
        ROOT_BG_COLOR = "#E8F0F2"  # Ana pencere için çok açık mavi/gri
        BG_COLOR = "#FDFEFE"       # Widget'lar için genel arka plan (neredeyse beyaz)
        FG_COLOR = "#2C3E50"       # Metinler için koyu mavi/gri
        ACCENT_COLOR = "#5DADE2"   # Vurgu için açık mavi
        ACCENT_HOVER_COLOR = "#85C1E9" # Vurgu hover için biraz daha açık mavi
        FG_ON_ACCENT = "#FFFFFF"   # Vurgu rengi üzerindeki metin (beyaz)
        
        FRAME_BG_COLOR = "#FFFFFF" # Frame içerikleri için beyaz
        BUTTON_BG_COLOR = "#D5DBDB" # Standart butonlar için açık gri
        BUTTON_FG_COLOR = "#2C3E50"   # Standart buton metni
        BUTTON_ACTIVE_BG_COLOR = "#AEB6BF" # Standart buton aktif/hover için orta gri
        
        BORDER_COLOR = "#AAB7B8"   # Kenarlıklar için gri
        STATUS_FG_COLOR = "#566573" # Durum etiketi metni için orta koyu gri
        
        COMBO_FIELD_BG = "#FFFFFF"
        COMBO_SELECT_BG = "#D5DBDB" # Combobox seçili öğe arka planı
        
        SCALE_TROUGH_COLOR = "#D5DBDB" # Scale trough rengi
        PROGRESSBAR_BG = ACCENT_COLOR # Progressbar dolgu rengi (Açık Mavi)
        PROGRESSBAR_TROUGH_COLOR = "#D5DBDB" # Progressbar trough rengi

        self.LED_ON_COLOR = "#2ECC71"  # LED açıkken (yeşil)
        self.LED_OFF_COLOR = "#D5DBDB" # LED kapalıyken (açık gri) - Buton rengine uygun hale getirildi

        self.root.configure(bg=ROOT_BG_COLOR) # Ana pencere arka planı

        style.theme_use('clam') # Modern bir tema tabanı

        style.configure("TFrame", background=BG_COLOR)
        style.configure("TLabel", background=BG_COLOR, foreground=FG_COLOR, font=("Arial", 11))
        style.configure("Title.TLabel", background=BG_COLOR, foreground=ACCENT_COLOR, font=("Arial", 24, "bold")) # DOMU Başlık
        style.configure("Status.TLabel", background=BG_COLOR, foreground=STATUS_FG_COLOR, font=("Arial", 10)) # Durum etiketi

        style.configure("TButton", 
                        background=BUTTON_BG_COLOR, 
                        foreground=BUTTON_FG_COLOR, 
                        font=("Arial", 10, "bold"), 
                        padding=6,
                        relief="flat",
                        borderwidth=0)
        style.map("TButton", 
                  background=[("active", BUTTON_ACTIVE_BG_COLOR), ("pressed", BUTTON_ACTIVE_BG_COLOR)],
                  relief=[("pressed", "sunken"), ("!pressed", "flat")])
        
        style.configure("Connect.TButton", background=ACCENT_COLOR, foreground=FG_ON_ACCENT)
        style.map("Connect.TButton", background=[("active", ACCENT_HOVER_COLOR)])
        
        # LED butonları için özel stiller
        style.configure("LED.Off.TButton", 
                        background=self.LED_OFF_COLOR, 
                        foreground=BUTTON_FG_COLOR,
                        font=("Arial", 10, "bold"),
                        padding=8,
                        relief="flat",
                        borderwidth=0)
        style.map("LED.Off.TButton", 
                  background=[("active", BUTTON_ACTIVE_BG_COLOR), ("pressed", BUTTON_ACTIVE_BG_COLOR)],
                  relief=[("pressed", "sunken"), ("!pressed", "flat")])
        
        style.configure("LED.On.TButton", 
                        background=self.LED_ON_COLOR, 
                        foreground=FG_ON_ACCENT,
                        font=("Arial", 10, "bold"),
                        padding=8,
                        relief="flat",
                        borderwidth=0)
        style.map("LED.On.TButton", 
                  background=[("active", "#27AE60"), ("pressed", "#27AE60")],  # Koyu yeşil tonlar
                  relief=[("pressed", "sunken"), ("!pressed", "flat")])
                  
        # HVAC modu butonları için özel stiller
        style.configure("Heating.TButton", 
                        background="#E74C3C",
                        foreground="white",
                        font=("Arial", 10, "bold"),
                        padding=6)
        style.map("Heating.TButton",
                  background=[("active", "#C0392B"), ("pressed", "#C0392B")],
                  relief=[("pressed", "sunken"), ("!pressed", "flat")])
                  
        style.configure("Cooling.TButton", 
                        background="#3498DB",
                        foreground="white",
                        font=("Arial", 10, "bold"),
                        padding=6)
        style.map("Cooling.TButton",
                  background=[("active", "#2980B9"), ("pressed", "#2980B9")],
                  relief=[("pressed", "sunken"), ("!pressed", "flat")])
                  
        style.configure("Comfort.TButton", 
                        background="#2ECC71",
                        foreground="white",
                        font=("Arial", 10, "bold"),
                        padding=6)
        style.map("Comfort.TButton",
                  background=[("active", "#27AE60"), ("pressed", "#27AE60")],
                  relief=[("pressed", "sunken"), ("!pressed", "flat")])

        style.configure("TLabelFrame", background=BG_COLOR, relief="solid", borderwidth=1) # bordercolor TLabelFrame'de doğrudan yok, relief ile gelir
        style.configure("TLabelFrame.Label", background=BG_COLOR, foreground=ACCENT_COLOR, font=("Arial", 14, "bold"))

        style.configure("TCombobox", 
                        fieldbackground=COMBO_FIELD_BG, 
                        background=BUTTON_BG_COLOR, # Combobox buton kısmı
                        foreground=FG_COLOR, # Combobox metni
                        arrowcolor=FG_COLOR, # Ok rengi
                        selectbackground=COMBO_SELECT_BG, # Açılır liste seçili öğe arka planı
                        selectforeground=ACCENT_COLOR, # Açılır liste seçili öğe metni (Açık Mavi)
                        font=("Arial", 10))
        style.map("TCombobox",
                  fieldbackground=[("readonly", COMBO_FIELD_BG)],
                  # selectbackground=[("readonly", COMBO_SELECT_BG)], # Bu satır bazen sorun çıkarabilir, gerekirse kaldırılabilir
                  # selectforeground=[("readonly", ACCENT_COLOR)] # Bu satır bazen sorun çıkarabilir
                  )

        style.configure("Horizontal.TScale", background=BG_COLOR, troughcolor=SCALE_TROUGH_COLOR)
        # Scale thumb'ı için daha detaylı stil gerekebilir, ttk varsayılanını kullanır.

        style.configure("TSpinbox",
                        fieldbackground=COMBO_FIELD_BG,
                        background=BUTTON_BG_COLOR, # Spinbox butonları
                        foreground=FG_COLOR,
                        arrowcolor=FG_COLOR,
                        font=("Arial", 10))
        
        style.configure("Horizontal.TProgressbar",
                        background=PROGRESSBAR_BG, # Dolgu rengi (Açık Mavi)
                        troughcolor=PROGRESSBAR_TROUGH_COLOR,
                        bordercolor=PROGRESSBAR_TROUGH_COLOR, 
                        lightcolor=PROGRESSBAR_BG, 
                        darkcolor=PROGRESSBAR_BG)

        # Ana frame
        main_frame = ttk.Frame(self.root, padding="8")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # DOMU başlık - daha küçük
        title_label = ttk.Label(main_frame, text="DOMU - Ev Otomasyonu Kontrol Paneli", style="Title.TLabel")
        title_label.pack(pady=(8, 12))

        # Seri port bağlantı bölümü
        connection_frame = ttk.LabelFrame(main_frame, text="Seri Port Bağlantısı")
        connection_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(connection_frame, text="Port:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.port_combo = ttk.Combobox(connection_frame, width=30)
        self.port_combo.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

        self.connect_button = ttk.Button(connection_frame, text="Bağlan", command=self.toggle_connection, style="Connect.TButton")
        self.connect_button.grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)

        # Üst satır bölümleri: Tarih/Hava Durumu ve Ziyaretçi yan yana
        top_row_frame = ttk.Frame(main_frame)
        top_row_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Tarih ve Hava Durumu bölümü (sol kısım)
        weather_frame = ttk.LabelFrame(top_row_frame, text="Tarih ve Hava Durumu")
        weather_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        top_row_frame.columnconfigure(0, weight=2)  # Hava durumu 2 birim
        
        # Tarih ve Hava Durumu İçeriği - kompakt tasarım
        weather_info_frame = ttk.Frame(weather_frame)
        weather_info_frame.pack(fill=tk.X, padx=3, pady=3)
        
        # Tarih ve sıcaklığı yan yana göster - daha az boşluk
        ttk.Label(weather_info_frame, text="Tarih:", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=2, pady=1, sticky=tk.W)
        ttk.Label(weather_info_frame, text=self.current_date, font=("Arial", 10)).grid(row=0, column=1, padx=2, pady=1, sticky=tk.W)
        
        # Saat bilgisini ekle
        ttk.Label(weather_info_frame, text="Saat:", font=("Arial", 10, "bold")).grid(row=1, column=0, padx=2, pady=1, sticky=tk.W)
        self.time_label = ttk.Label(weather_info_frame, textvariable=self.current_time, font=("Arial", 10))
        self.time_label.grid(row=1, column=1, padx=2, pady=1, sticky=tk.W)
        
        ttk.Label(weather_info_frame, text="Sıcaklık:", font=("Arial", 10, "bold")).grid(row=2, column=0, padx=2, pady=1, sticky=tk.W)
        ttk.Label(weather_info_frame, textvariable=self.temperature, font=("Arial", 10)).grid(row=2, column=1, padx=2, pady=1, sticky=tk.W)
        
        ttk.Label(weather_info_frame, text="Durum:", font=("Arial", 10, "bold")).grid(row=3, column=0, padx=2, pady=1, sticky=tk.W)
        ttk.Label(weather_info_frame, textvariable=self.weather_condition, font=("Arial", 10)).grid(row=3, column=1, padx=2, pady=1, sticky=tk.W)
        
        # Güncelleme bilgisi ve butonu kompakt
        update_info_frame = ttk.Frame(weather_frame)
        update_info_frame.pack(fill=tk.X, padx=3, pady=(0, 2))
        
        ttk.Label(update_info_frame, text="Son Güncelleme:", font=("Arial", 8)).grid(row=0, column=0, padx=2, pady=1, sticky=tk.W)
        ttk.Label(update_info_frame, textvariable=self.weather_update_time, font=("Arial", 8)).grid(row=0, column=1, padx=2, pady=1, sticky=tk.W)
        
        update_weather_button = ttk.Button(weather_frame, text="Hava Durumunu Güncelle", 
                                          command=self.update_weather_info, 
                                          width=16)
        update_weather_button.pack(anchor=tk.W, padx=3, pady=(0, 2))
        
        # Ziyaretçi bölümü (sağ kısım) - kompakt
        visitor_frame = ttk.LabelFrame(top_row_frame, text="Ziyaretçi")
        visitor_frame.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        self.visitor_count = 0  # Ziyaretçi sayacı
        self.visitor_label = ttk.Label(visitor_frame, text="Toplam Ziyaretçi: 0", font=("Arial", 14))
        self.visitor_label.pack(anchor=tk.CENTER, padx=3, pady=6)
        
        # Kapı Kontrolü ve Havalandırma yan yana
        mid_row_frame = ttk.Frame(main_frame)
        mid_row_frame.pack(fill=tk.X, padx=5, pady=3)
        mid_row_frame.columnconfigure(0, weight=1)  # Kapı kontrolü 1 birim
        mid_row_frame.columnconfigure(1, weight=1)  # HVAC kontrolü 1 birim
        # Kapı Kontrolü bölümü (sol kısım)
        door_frame = ttk.LabelFrame(mid_row_frame, text="Kapı Kontrolü")
        door_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        door_buttons_frame = ttk.Frame(door_frame)
        door_buttons_frame.pack(fill=tk.X, padx=3, pady=3)
        door_buttons_frame.columnconfigure(0, weight=1)
        door_buttons_frame.columnconfigure(1, weight=1)
        
        self.open_door_button = ttk.Button(door_buttons_frame, text="Kapıyı Aç", 
                                         command=self.open_door,
                                         width=10)
        self.open_door_button.grid(row=0, column=0, padx=3, pady=3, sticky="ew")
        
        self.close_door_button = ttk.Button(door_buttons_frame, text="Kapıyı Kapat", 
                                          command=self.close_door,
                                          width=10)
        self.close_door_button.grid(row=0, column=1, padx=3, pady=3, sticky="ew")
        
        # Havalandırma Kontrolü bölümü - daha kompakt tasarım
        hvac_frame = ttk.LabelFrame(mid_row_frame, text="Havalandırma Kontrolü")
        hvac_frame.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # İlk satır: Sıcaklık etiketi ve durum yan yana
        hvac_top_frame = ttk.Frame(hvac_frame)
        hvac_top_frame.pack(fill=tk.X, padx=2, pady=1)
        hvac_top_frame.columnconfigure(0, weight=1)
        hvac_top_frame.columnconfigure(1, weight=1)
        
        self.temp_label = ttk.Label(hvac_top_frame, text="Hedef Sıcaklık: -- °C", font=("Arial", 11))
        self.temp_label.grid(row=0, column=0, padx=2, pady=1, sticky="w")
        
        self.hvac_status = ttk.Label(hvac_top_frame, text="Durum: Beklemede", font=("Arial", 9))
        self.hvac_status.grid(row=0, column=1, padx=2, pady=1, sticky="e")
        
        # Progress bar ve HVAC modu butonu yan yana
        hvac_mid_frame = ttk.Frame(hvac_frame)
        hvac_mid_frame.pack(fill=tk.X, padx=2, pady=1)
        hvac_mid_frame.columnconfigure(0, weight=2)
        hvac_mid_frame.columnconfigure(1, weight=1)
        
        self.pot_progress = ttk.Progressbar(hvac_mid_frame, length=120, maximum=1023, variable=self.pot_value, style="Horizontal.TProgressbar")
        self.pot_progress.grid(row=0, column=0, padx=2, pady=1, sticky="ew")
        
        # HVAC modu butonu
        self.hvac_mode_button = ttk.Button(hvac_mid_frame, text="", width=10)
        self.hvac_mode_button.grid(row=0, column=1, padx=2, pady=1, sticky="e")
        
        # Butonlar yan yana
        hvac_buttons_frame = ttk.Frame(hvac_frame)
        hvac_buttons_frame.pack(fill=tk.X, padx=2, pady=1)
        hvac_buttons_frame.columnconfigure(0, weight=1)
        hvac_buttons_frame.columnconfigure(1, weight=1)
        
        self.update_temp_button = ttk.Button(hvac_buttons_frame, text="Hedef Sıcaklığı Oku", 
                                      command=self.request_pot_value,
                                      width=12)
        self.update_temp_button.grid(row=0, column=0, padx=2, pady=1, sticky="w")
        
        self.auto_update_button = ttk.Button(hvac_buttons_frame, text="Oto Güncelle", 
                                      command=self.toggle_auto_update_temp,
                                      width=10)
        self.auto_update_button.grid(row=0, column=1, padx=2, pady=1, sticky="e")
        
        # Ev Işığı Kontrolü bölümü
        led_frame = ttk.LabelFrame(main_frame, text="Ev Işığı Kontrolü")
        led_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.led_buttons = []
        self.led_names = ["Mutfak", "Koridor", "Yatak Odası", "Oturma Odası"] # LED isimleri
        self.led_status = [False, False, False, False]  # LED durumları
        
        # Butonlar için bir grid oluştur
        led_grid = ttk.Frame(led_frame)
        led_grid.pack(fill=tk.X, padx=5, pady=5)
        
        # Sütunların genişliklerini ayarla
        led_grid.columnconfigure(0, weight=1)  
        led_grid.columnconfigure(1, weight=1)
        
        # Butonları 2x2 grid olarak göster - daha kompakt yerleşim
        for i in range(4):
            row = i // 2  # İlk iki buton ilk satırda, sonraki ikisi ikinci satırda
            col = i % 2   # 0 ve 2 ilk sütunda, 1 ve 3 ikinci sütunda
            
            led_button = ttk.Button(led_grid, text=self.led_names[i], 
                                  command=lambda idx=i: self.toggle_led(idx),
                                  style="LED.Off.TButton",
                                  width=12) # Daha küçük butonlar
            led_button.grid(row=row, column=col, padx=3, pady=3, sticky="ew") # Daha az boşluk
            self.led_buttons.append(led_button)

        # Durum bilgisi
        self.status_label = ttk.Label(main_frame, text="Durum: Bağlantı bekleniyor...", style="Status.TLabel")
        self.status_label.pack(anchor=tk.S, side=tk.BOTTOM, pady=5, fill=tk.X)

        # Port listesini güncelleme
        self.update_ports()

        # Periyodik port güncellemesi
        self.root.after(2000, self.periodic_update_ports)
        
        # İlk hava durumu güncellemesi
        self.root.after(1000, self.update_weather_info)
        
        # Saat güncellemesini başlat
        self.update_time()

    def update_ports(self):
        # Mevcut port seçimini hatırla
        current_port = self.port_combo.get()
        
        # Port listesini güncelle
        self.port_combo['values'] = [port.device for port in serial.tools.list_ports.comports()]
        
        # Önceki port hala varsa, onu seç
        if current_port in self.port_combo['values']:
            self.port_combo.set(current_port)
        elif len(self.port_combo['values']) > 0:
            self.port_combo.current(0)
    
    def periodic_update_ports(self):
        # Bağlantı yoksa portları güncelle
        if not self.connected:
            self.update_ports()
        # Her 2 saniyede bir kontrol et
        self.root.after(2000, self.periodic_update_ports)
    
    def update_hvac_status(self, temperature):
        """Sıcaklık değerine göre HVAC durumunu günceller."""
        self.temp_label.config(text=f"Sıcaklık: {temperature} °C")
        
        # Sıcaklığa göre HVAC durumunu belirle
        if temperature < 18:
            status = "Isıtma Aktif"
            status_text = f"Durum: {status} (Düşük Sıcaklık)"
        elif temperature > 26:
            status = "Soğutma Aktif"
            status_text = f"Durum: {status} (Yüksek Sıcaklık)"
        else:
            status = "İdeal Sıcaklık"
            status_text = f"Durum: {status} (Konforlu)"
            
        # HVAC durum etiketini güncelle
        self.hvac_status.config(text=status_text)
    
    def toggle_connection(self):
        if not self.connected:
            try:
                port = self.port_combo.get()
                if not port:
                    messagebox.showwarning("Hata", "Lütfen bir seri port seçin.")
                    return
                
                self.serial_port = serial.Serial(port, 9600, timeout=1)
                time.sleep(2) # Arduino'nun reset olması için bekle
                
                self.connect_button.config(text="Bağlantıyı Kes")
                self.status_label.config(text=f"Durum: {port} portuna bağlandı")
                self.connected = True
                
                # Seri veri okuma thread'ini başlat
                self.stop_thread = False
                self.reading_thread = threading.Thread(target=self.read_serial_data)
                self.reading_thread.daemon = True
                self.reading_thread.start()
                
                # Arduino'dan mevcut durum bilgisini iste
                self.request_pot_value()
                
            except Exception as e:
                messagebox.showerror("Bağlantı Hatası", f"Seri porta bağlanırken hata oluştu: {str(e)}")
                self.serial_port = None
        else:
            # Thread'i durdur
            self.stop_thread = True
            if self.reading_thread:
                self.reading_thread.join(timeout=1.0)
            
            # Bağlantıyı kapat
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
            
            self.serial_port = None
            self.connect_button.config(text="Bağlan")
            self.status_label.config(text="Durum: Bağlantı kesildi")
            self.connected = False
    
    def toggle_led(self, led_index):
        if not self.check_connection():
            return
        
        try:
            # Arduino'ya LED komutunu gönder
            command = f"LED:{led_index}\n"
            self.serial_port.write(command.encode())
            # Durum etiketini komut gönderildi olarak güncelle, Arduino'dan yanıt bekleniyor
            self.status_label.config(text=f"Durum: {self.led_names[led_index]} için komut gönderildi...")

        except Exception as e:
            messagebox.showwarning("Hata", f"LED kontrol edilirken hata: {str(e)}")
    
    def request_pot_value(self):
        """Potansiyometre değerini ister ve hedef sıcaklık olarak gösterir."""
        if not self.check_connection():
            return
            
        try:
            command = "GET_POT\n"
            self.serial_port.write(command.encode())
            self.status_label.config(text="Durum: Hedef sıcaklık bilgisi istendi")
            
        except Exception as e:
            messagebox.showwarning("Hata", f"Hedef sıcaklık bilgisi istenirken hata: {str(e)}")
    
    def toggle_auto_update_temp(self):
        """Otomatik sıcaklık güncellemeyi açar veya kapatır."""
        self.auto_update_temp = not self.auto_update_temp
        
        if self.auto_update_temp:
            # Otomatik güncellemeyi başlat
            self.status_label.config(text="Durum: Otomatik hedef sıcaklık güncelleme açıldı")
            self.hvac_status.config(text="Durum: Otomatik güncellemede")
            self.auto_update_button.config(text="Otomatik Kapat")
            self.update_temp_button.config(state="disabled")  # Manuel butonunu devre dışı bırak
            self.auto_update_job = self.root.after(1000, self.auto_update_temperature)
        else:
            # Otomatik güncellemeyi durdur
            if self.auto_update_job:
                self.root.after_cancel(self.auto_update_job)
                self.auto_update_job = None
            self.status_label.config(text="Durum: Otomatik hedef sıcaklık güncelleme kapatıldı")
            self.hvac_status.config(text="Durum: Beklemede")
            self.auto_update_button.config(text="Otomatik Güncelle")
            self.update_temp_button.config(state="normal")  # Manuel butonunu etkinleştir
    
    def auto_update_temperature(self):
        """Periyodik olarak sıcaklık değerini günceller."""
        if self.connected and self.auto_update_temp:
            self.request_pot_value()
            # 1 saniyede bir tekrarla
            self.auto_update_job = self.root.after(1000, self.auto_update_temperature)
    
    def read_serial_data(self):
        while not self.stop_thread:
            if not self.serial_port or not self.serial_port.is_open:
                time.sleep(0.1)
                continue
                
            try:
                if self.serial_port.in_waiting:
                    data = self.serial_port.readline().decode('utf-8').strip()
                    
                    if data.startswith("POT:"):
                        pot_value = int(data[4:])
                        self.pot_value.set(pot_value)
                        
                        # Potansiyometre değerini istenen oda sıcaklığına dönüştür (15-30°C arasında)
                        desired_temp = 15 + (pot_value / 1023) * 15
                        formatted_temp = round(desired_temp, 1)
                        
                        # Sıcaklık ve HVAC durumunu güncelle
                        self.root.after(0, lambda: self.update_hvac_status(formatted_temp))
                        
                    elif data.startswith("LED_OK:"): # Arduino'dan LED durum onayı geldiğinde
                        led_index = int(data[7:])
                        # LED durumunu tersine çevir
                        self.led_status[led_index] = not self.led_status[led_index]
                        # UI'ı güncelle - buton stilini değiştir
                        led_idx = led_index  # Değişkeni kopyala
                        self.root.after(0, lambda: self.update_led_indicators_and_status(led_idx))
                            
                    elif data == "BUTTON_PRESSED":
                        # Butona basıldığında kamerayı aç ve popup göster
                        self.root.after(0, self.open_camera_and_show_popup)
                        
                    elif data == "DOOR_OPENED":
                        self.door_open = True
                        self.root.after(0, lambda: self.status_label.config(text="Durum: Kapı açıldı"))
                        
                    elif data == "DOOR_CLOSED":
                        self.door_open = False
                        self.root.after(0, lambda: self.status_label.config(text="Durum: Kapı kapandı"))
                        
            except Exception as e:
                print(f"Seri veri okuma hatası: {str(e)}")
                
            time.sleep(0.1)  # CPU kullanımını azaltmak için kısa bekleme
    
    def open_camera_and_show_popup(self):
        """Kamerayı açar ve kapı açma popup'ını gösterir."""
        try:
            # Cheese kamera uygulamasını başlat (arka planda)
            subprocess.Popen(["cheese"])
            self.status_label.config(text="Durum: Kamera açıldı")
            
            # Popup göster
            self.show_door_popup()
        except Exception as e:
            messagebox.showerror("Hata", f"Kamera açılırken hata oluştu: {str(e)}")
    
    def show_door_popup(self):
        """Kapı açma popup'ını gösterir."""
        response = messagebox.askyesno("Kapı Kontrolü", "Kapı açılsın mı?")
        if response:
            # Evete basıldıysa, kapıyı aç
            self.open_door()
    
    def open_door(self):
        """Kapıyı açmak için Arduino'ya komut gönderir."""
        if not self.check_connection():
            return
            
        try:
            if not self.door_open:  # Kapı zaten açık değilse
                command = "OPEN_DOOR\n"
                self.serial_port.write(command.encode())
                self.status_label.config(text="Durum: Kapı açılıyor... (5 saniye sonra kapanacak)")
                self.door_open = True
                
                # Ziyaretçi sayacını arttır
                self.increment_visitor_count()
                
                # 5 saniye sonra kapıyı otomatik kapat
                self.root.after(5000, self.auto_close_door)
            else:
                self.status_label.config(text="Durum: Kapı zaten açık")
            
        except Exception as e:
            messagebox.showwarning("Hata", f"Kapı açılırken hata: {str(e)}")
    
    def close_door(self):
        """Kapıyı kapatmak için Arduino'ya komut gönderir."""
        if not self.check_connection():
            return
            
        try:
            if self.door_open:  # Kapı açıksa
                command = "CLOSE_DOOR\n"
                self.serial_port.write(command.encode())
                self.status_label.config(text="Durum: Kapı kapanıyor...")
                self.door_open = False
            else:
                self.status_label.config(text="Durum: Kapı zaten kapalı")
            
        except Exception as e:
            messagebox.showwarning("Hata", f"Kapı kapatılırken hata: {str(e)}")
    
    def auto_close_door(self):
        """Kapıyı otomatik olarak kapatır."""
        if self.door_open:  # Kapı hala açıksa
            try:
                if self.serial_port and self.serial_port.is_open:
                    command = "CLOSE_DOOR\n"
                    self.serial_port.write(command.encode())
                    self.status_label.config(text="Durum: Kapı otomatik kapanıyor...")
                    self.door_open = False
            except Exception as e:
                print(f"Otomatik kapı kapatma hatası: {str(e)}")
    
    def increment_visitor_count(self):
        """Ziyaretçi sayacını bir arttırır ve etiketi günceller."""
        self.visitor_count += 1
        self.visitor_label.config(text=f"Toplam Ziyaretçi: {self.visitor_count}")
        self.status_label.config(text=f"Durum: Yeni ziyaretçi geldi (Toplam: {self.visitor_count})")
    
    def update_led_indicators_and_status(self, led_index):
        """Belirtilen LED'in buton rengini ve durum etiketini günceller."""
        # Bu metod sadece başka bir thread tarafından çağrıldığında
        # led_index değişkeninin doğru değeri alabilmesi için bir wrapper işlevi görür
        led_index_actual = led_index  # Yerel bir değişkene kopyala
        
        if self.led_status[led_index_actual]:
            # LED açıksa buton stilini değiştir
            self.led_buttons[led_index_actual].configure(style="LED.On.TButton")
            self.status_label.config(text=f"Durum: {self.led_names[led_index_actual]} açıldı")
        else:
            # LED kapalıysa buton stilini değiştir
            self.led_buttons[led_index_actual].configure(style="LED.Off.TButton")
            self.status_label.config(text=f"Durum: {self.led_names[led_index_actual]} kapatıldı")
            
    def update_hvac_status(self, temperature):
        """Sıcaklık değerine göre HVAC durumunu günceller."""
        self.temp_label.config(text=f"Hedef Sıcaklık: {temperature} °C")
        
        # Dışarıdaki hava sıcaklığını al (hava durumundan)
        outside_temp = 0
        try:
            # Hava durumu sıcaklığı formattan çıkar (ör: "25.5 °C" -> 25.5)
            outside_temp_str = self.temperature.get().replace(" °C", "")
            outside_temp = float(outside_temp_str)
        except:
            outside_temp = temperature  # Hava durumu verisi yoksa sensör verisini kullan
        
        # Sıcaklığa göre HVAC durumunu belirle
        if temperature < outside_temp:  # İstenilen oda sıcaklığı dışarıdan düşükse
            status = "Soğutma Aktif"
            status_text = f"Durum: {status} (Dış sıcaklık: {outside_temp}°C)"
            hvac_mode = "Soğutma"
            button_color = "#3498DB"  # Mavi
        elif temperature > outside_temp:  # İstenilen oda sıcaklığı dışarıdan yüksekse
            status = "Isıtma Aktif"
            status_text = f"Durum: {status} (Dış sıcaklık: {outside_temp}°C)"
            hvac_mode = "Isıtma"
            button_color = "#E74C3C"  # Kırmızı
        else:
            status = "İdeal Sıcaklık"
            status_text = f"Durum: {status} (Dış sıcaklık: {outside_temp}°C)"
            hvac_mode = "Konfor"
            button_color = "#2ECC71"  # Yeşil
            
        # HVAC durum etiketini güncelle
        self.hvac_status.config(text=status_text)
        
        # HVAC modu butonunu güncelle - ttk.Button için özel stil tanımlama
        self.hvac_mode_button.config(text=hvac_mode)
        
        # Buton stilini dinamik olarak ayarla
        if hvac_mode == "Isıtma":
            self.hvac_mode_button.configure(style="Heating.TButton")
        elif hvac_mode == "Soğutma":
            self.hvac_mode_button.configure(style="Cooling.TButton")
        else:
            self.hvac_mode_button.configure(style="Comfort.TButton")

    def check_connection(self):
        if not self.serial_port or not self.serial_port.is_open:
            messagebox.showwarning("Bağlantı Hatası", "Arduino'ya bağlı değilsiniz.")
            return False
        return True
    
    def on_closing(self):
        # Thread'i durdur
        self.stop_thread = True
        if self.reading_thread:
            self.reading_thread.join(timeout=1.0)
        
        # Otomatik güncellemeyi durdur
        if self.auto_update_job:
            self.root.after_cancel(self.auto_update_job)
        
        # Bağlantıyı kapat
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        
        # Uygulamayı kapat
        self.root.destroy()

    def update_weather_info(self):
        """Hava durumu bilgilerini manuel olarak günceller."""
        try:
            # Manuel hava durumu bilgileri (API yerine sabit değerler kullanılıyor)
            current_date = datetime.datetime.now()
            
            # Mevsimden bağımsız olarak 0-35 derece arası sıcaklık değerleri
            temp = round(random.uniform(0.0, 35.0), 1)  # 0-35 derece arası rastgele
            
            # Mevsime göre farklı hava durumu koşulları
            month = current_date.month
            if month in [5, 6, 7, 8, 9]:  # Yaz ayları
                conditions = ["Güneşli", "Parçalı bulutlu", "Az bulutlu", "Açık"]
            else:  # Kış ayları
                conditions = ["Bulutlu", "Yağmurlu", "Parçalı bulutlu", "Kapalı"]
                
            condition = random.choice(conditions)
            
            # Değişkenleri güncelle
            self.temperature.set(f"{temp} °C")
            self.weather_condition.set(condition)
            self.weather_update_time.set(current_date.strftime("%H:%M"))
            
            self.status_label.config(text=f"Durum: Hava durumu bilgileri güncellendi ({self.weather_update_time.get()})")
        except Exception as e:
            print(f"Hava durumu güncellenirken hata: {str(e)}")
    
    def update_time(self):
        """Saat bilgisini periyodik olarak günceller."""
        try:
            # Güncel saati al ve göster
            current_time = datetime.datetime.now().strftime("%H:%M:%S")
            self.current_time.set(current_time)
            
            # Her 1 saniyede bir güncelle
            self.root.after(1000, self.update_time)
        except Exception as e:
            print(f"Saat güncellenirken hata: {str(e)}")
            # Hata olsa bile güncellemeye devam et
            self.root.after(1000, self.update_time)
        
        # Otomatik güncelleme kaldırıldı
        # self.root.after(30 * 60 * 1000, self.update_weather_info)

if __name__ == "__main__":
    root = tk.Tk()
    app = ArduinoControlGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
