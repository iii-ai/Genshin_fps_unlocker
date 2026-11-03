# -*- coding: utf-8 -*-
"""
app.py — GenshinUnlocker · 图形界面（v1.0.0）

布局参考 FlClash：左侧可收起的图标侧栏 + 右侧卡片式主区。
状态环用 Pillow 超采样渲染；浅色 / 灰黑色 / 跟随系统三套皮肤；九种界面语言。
"""

import ctypes
import json
import math
import os
import queue
import sys
import threading
import time
import tkinter as tk
from tkinter import filedialog

import core

try:
    from PIL import Image, ImageDraw, ImageTk
    HAS_PIL = True
except Exception:
    HAS_PIL = False

VERSION = "v1.0.0"
REPOSITORY_URL = "https://github.com/iii-ai/Genshin_fps_unlocker"
UPDATED = "2026-11-3"

THEMES = {
    "light": dict(
        BG="#f3f5f9", CARD="#ffffff", HOVER="#edf1f8", TEXT="#202b40",
        SIDE="#f9fafe", SIDE_LINE="#e2e7f0",
        SUB="#596880", MUTED="#69778e", LINE="#e2e7f0", TRACK="#e7ecf5",
        SEL_BG="#ffffff", DROP_BG="#ffffff", DROP_HOVER="#f0f0f2",
        PLACE="#c7c7cc", GLOW="#dceafc", TINT="#c9e0ff",
        BLUE="#2563db", BLUE_HI="#3976ed",
        GREEN="#34c759", GREEN_TX="#1d9a4e",
        RED="#ff3b30", RED_TX="#d70015", RED_FILL="#ff453a", RED_FILL_HI="#ff6961",
    ),
    "dark": dict(
        BG="#101620", CARD="#192230", HOVER="#243146", TEXT="#eef3fc",
        SIDE="#141c28", SIDE_LINE="#273345",
        SUB="#b0bdd0", MUTED="#8f9fb6", LINE="#2a374b", TRACK="#2c3b52",
        SEL_BG="#202d40", DROP_BG="#202d40", DROP_HOVER="#2a3b55",
        PLACE="#54555c", GLOW="#16283c", TINT="#2b5588",
        BLUE="#3274ee", BLUE_HI="#4988ff",
        GREEN="#30d158", GREEN_TX="#4cd97b",
        RED="#ff453a", RED_TX="#ff6961", RED_FILL="#ff453a", RED_FILL_HI="#ff6961",
    ),
}


BG = CARD = HOVER = TEXT = SUB = MUTED = LINE = TRACK = ""
SEL_BG = DROP_BG = DROP_HOVER = PLACE = GLOW = TINT = ""
BLUE = BLUE_HI = GREEN = GREEN_TX = RED = RED_TX = RED_FILL = RED_FILL_HI = ""
SIDE = SIDE_LINE = ""

FONT = "Microsoft YaHei UI"
NUM = "TkDefaultFont"

W, H = 1128, 711
SIDE_W, SIDE_MINI = 220, 64
PAD = 26
FPS_STOPS = ((120, "120"), (144, "144"), (200, "200"), (240, "240"),
             (1000, "\u221e"))

LANGS = (
    ("zh-CN", "简体中文"),
    ("zh-HK", "繁體中文（香港）"),
    ("zh-TW", "繁體中文（台灣）"),
    ("en", "English"),
    ("ru", "Русский"),
    ("de", "Deutsch"),
    ("ja", "日本語"),
    ("fr", "Français"),
    ("ko", "한국어"),
)

T = {
    "zh-CN": dict(
        start="启动游戏并解锁", stop="停止", busy_btn="处理中…", retry="重试",
        s_idle="待机", s_idle_sub="未启动", s_busy="处理中",
        s_busy_sub="正在接管游戏进程", s_ok="解锁成功", s_ok_sub="已生效 · {fps}",
        s_fail="解锁失败", s_fail_sub="未能接管游戏进程",
        stat_target="目标帧率", stat_pid="游戏进程", stat_patch="加固状态",
        patch_on="已加固", patch_off="未加固",
        nav_skin="皮肤设置", nav_fps="修改帧率", nav_cfg="配置",
        nav_lang="语言", nav_about="关于",
        sub_skin="选择界面背景与配色", sub_fps="启动时写入的目标帧率",
        sub_cfg="游戏路径与启动偏好", sub_lang="选择界面语言",
        sub_about="版本与说明",
        appearance="外观", theme_light="浅色", theme_dark="深色",
        theme_auto="跟随系统", fps_target="目标帧率", unlimited="无上限",
        game_exe="游戏程序", auto_search="自动搜索",
        imported="已导入：{p}", not_imported="尚未导入游戏程序",
        searching="正在搜索…", found_import="已找到并导入：\n{p}",
        not_found="没找到，请手动选择 YuanShen.exe",
        version="版本", updated="更新时间", language="语言",
        err_no_exe="游戏程序无效 · 请到 设置 · 配置 里指定 YuanShen.exe",
        err_fps="帧率请填 60 – 1000 之间的整数",
        err_admin="游戏需要管理员权限 · 请以管理员身份运行本工具",
        err_access="无法打开游戏进程 · 请以管理员身份运行",
        dlg_title="选择游戏主程序", dlg_exe="游戏程序", dlg_all="全部文件",
    ),
    "zh-HK": dict(
        start="解鎖幀率", stop="停止", busy_btn="處理中…", retry="重試",
        s_idle="待機", s_idle_sub="未啟動", s_busy="處理中",
        s_busy_sub="正在接管遊戲進程", s_ok="解鎖成功", s_ok_sub="已生效 · {fps}",
        s_fail="解鎖失敗", s_fail_sub="未能接管遊戲進程",
        stat_target="目標幀率", stat_pid="遊戲進程", stat_patch="加固狀態",
        patch_on="已加固", patch_off="未加固",
        nav_skin="外觀設定", nav_fps="修改幀率", nav_cfg="設定",
        nav_lang="語言", nav_about="關於",
        sub_skin="選擇介面背景與配色", sub_fps="啟動時寫入的目標幀率",
        sub_cfg="遊戲路徑與啟動偏好", sub_lang="選擇介面語言",
        sub_about="版本與說明",
        appearance="外觀", theme_light="淺色", theme_dark="深色",
        theme_auto="跟隨系統", fps_target="目標幀率", unlimited="無上限",
        game_exe="遊戲程式", auto_search="自動搜尋",
        imported="已匯入：{p}", not_imported="尚未匯入遊戲程式",
        searching="正在搜尋…", found_import="已找到並匯入：\n{p}",
        not_found="找不到，請手動選擇 YuanShen.exe",
        version="版本", updated="更新時間", language="語言",
        err_no_exe="遊戲程式無效 · 請到 設定 · 設定 指定 YuanShen.exe",
        err_fps="幀率請填 60 – 1000 之間的整數",
        err_admin="遊戲需要系統管理員權限 · 請以管理員身分執行本工具",
        err_access="無法開啟遊戲進程 · 請以管理員身分執行",
        dlg_title="選擇遊戲程式", dlg_exe="程式", dlg_all="所有檔案",
    ),
    "zh-TW": dict(
        start="解鎖幀率", stop="停止", busy_btn="處理中…", retry="重試",
        s_idle="待機", s_idle_sub="未啟動", s_busy="處理中",
        s_busy_sub="正在接管遊戲處理程序", s_ok="解鎖成功", s_ok_sub="已生效 · {fps}",
        s_fail="解鎖失敗", s_fail_sub="未能接管遊戲處理程序",
        stat_target="目標幀率", stat_pid="遊戲處理程序", stat_patch="加固狀態",
        patch_on="已加固", patch_off="未加固",
        nav_skin="外觀設定", nav_fps="修改幀率", nav_cfg="設定",
        nav_lang="語言", nav_about="關於",
        sub_skin="選擇介面背景與配色", sub_fps="啟動時寫入的目標幀率",
        sub_cfg="遊戲路徑與啟動偏好", sub_lang="選擇介面語言",
        sub_about="版本與說明",
        appearance="外觀", theme_light="淺色", theme_dark="深色",
        theme_auto="跟隨系統", fps_target="目標幀率", unlimited="無上限",
        game_exe="遊戲程式", auto_search="自動搜尋",
        imported="已匯入：{p}", not_imported="尚未匯入遊戲程式",
        searching="正在搜尋…", found_import="已找到並匯入：\n{p}",
        not_found="找不到，請手動選擇 YuanShen.exe",
        version="版本", updated="更新時間", language="語言",
        err_no_exe="遊戲程式無效 · 請到 設定 · 設定 指定 YuanShen.exe",
        err_fps="幀率請填 60 – 1000 之間的整數",
        err_admin="遊戲需要系統管理員權限 · 請以管理員身分執行本工具",
        err_access="無法開啟遊戲處理程序 · 請以管理員身分執行",
        dlg_title="選擇遊戲程式", dlg_exe="程式", dlg_all="所有檔案",
    ),
    "en": dict(
        start="Unlock framerate", stop="Stop", busy_btn="Working…", retry="Retry",
        s_idle="Idle", s_idle_sub="Not running", s_busy="Working",
        s_busy_sub="Taking over the game process", s_ok="Unlocked",
        s_ok_sub="Active · {fps}", s_fail="Unlock failed",
        s_fail_sub="Could not take over the game process",
        stat_target="Target", stat_pid="Process", stat_patch="Patch",
        patch_on="Patched", patch_off="Not patched",
        nav_skin="Appearance", nav_fps="Frame rate", nav_cfg="Configuration",
        nav_lang="Language", nav_about="About",
        sub_skin="Choose background and colors",
        sub_fps="Frame rate written at launch",
        sub_cfg="Game path and launch preferences",
        sub_lang="Choose the interface language", sub_about="Version and info",
        appearance="Appearance", theme_light="Light", theme_dark="Dark",
        theme_auto="Follow system", fps_target="Target frame rate",
        unlimited="Unlimited", game_exe="Game executable",
        auto_search="Auto search", imported="Imported: {p}",
        not_imported="No game imported yet", searching="Searching…",
        found_import="Found and imported:\n{p}",
        not_found="Not found. Please choose YuanShen.exe manually",
        version="Version", updated="Updated", language="Language",
        err_no_exe="Invalid game path · Set YuanShen.exe in Settings · Configuration",
        err_fps="Enter an integer between 60 and 1000",
        err_admin="The game requires administrator rights · Run this tool as administrator",
        err_access="Cannot open the game process · Run this tool as administrator",
        dlg_title="Select the game executable", dlg_exe="Executable",
        dlg_all="All files",
    ),
    "ru": dict(
        start="Разблокировать частоту", stop="Стоп", busy_btn="Обработка…",
        retry="Повторить", s_idle="Ожидание", s_idle_sub="Не запущено",
        s_busy="Обработка", s_busy_sub="Подключение к процессу игры",
        s_ok="Разблокировано", s_ok_sub="Активно · {fps}", s_fail="Ошибка",
        s_fail_sub="Не удалось подключиться к игре",
        stat_target="Цель", stat_pid="Процесс", stat_patch="Патч",
        patch_on="Пропатчено", patch_off="Без патча",
        nav_skin="Оформление", nav_fps="Частота кадров",
        nav_cfg="Конфигурация", nav_lang="Язык", nav_about="О программе",
        sub_skin="Фон и цветовая схема", sub_fps="Частота кадров при запуске",
        sub_cfg="Путь установки и параметры запуска",
        sub_lang="Язык интерфейса", sub_about="Версия и сведения",
        appearance="Оформление", theme_light="Светлая", theme_dark="Тёмная",
        theme_auto="Как в системе", fps_target="Целевая частота",
        unlimited="Без ограничения", game_exe="Файл игры",
        auto_search="Автопоиск", imported="Импортировано: {p}",
        not_imported="Игра не импортирована", searching="Поиск…",
        found_import="Найдено и импортировано:\n{p}",
        not_found="Не найдено. Выберите YuanShen.exe вручную",
        version="Версия", updated="Обновлено", language="Язык",
        err_no_exe="Неверный путь · Укажите YuanShen.exe в разделе «Конфигурация»",
        err_fps="Введите целое число от 60 до 1000",
        err_admin="Игре нужны права администратора · Запустите инструмент от имени администратора",
        err_access="Нет доступа к процессу игры · Запустите инструмент от имени администратора",
        dlg_title="Выберите файл игры", dlg_exe="Программы",
        dlg_all="Все файлы",
    ),
    "de": dict(
        start="Bildrate freischalten", stop="Stopp", busy_btn="Läuft…",
        retry="Erneut", s_idle="Bereit", s_idle_sub="Nicht gestartet",
        s_busy="Läuft", s_busy_sub="Übernehme Spielprozess",
        s_ok="Freigeschaltet", s_ok_sub="Aktiv · {fps}", s_fail="Fehlgeschlagen",
        s_fail_sub="Spielprozess konnte nicht übernommen werden",
        stat_target="Ziel", stat_pid="Prozess", stat_patch="Patch",
        patch_on="Gepatcht", patch_off="Ungeschützt",
        nav_skin="Darstellung", nav_fps="Bildrate", nav_cfg="Konfiguration",
        nav_lang="Sprache", nav_about="Über",
        sub_skin="Hintergrund und Farben", sub_fps="Beim Start gesetzte Bildrate",
        sub_cfg="Installationspfad und Startoptionen",
        sub_lang="Sprache der Oberfläche", sub_about="Version und Hinweise",
        appearance="Darstellung", theme_light="Hell", theme_dark="Dunkel",
        theme_auto="Wie System", fps_target="Zielbildrate",
        unlimited="Unbegrenzt", game_exe="Spieldatei",
        auto_search="Automatisch suchen", imported="Importiert: {p}",
        not_imported="Noch kein Spiel importiert", searching="Suche…",
        found_import="Gefunden und importiert:\n{p}",
        not_found="Nicht gefunden. Bitte YuanShen.exe manuell wählen",
        version="Version", updated="Aktualisiert", language="Sprache",
        err_no_exe="Ungültiger Pfad · YuanShen.exe unter Konfiguration wählen",
        err_fps="Ganzzahl zwischen 60 und 1000 eingeben",
        err_admin="Das Spiel benötigt Administratorrechte · Tool als Administrator ausführen",
        err_access="Kein Zugriff auf den Spielprozess · Tool als Administrator ausführen",
        dlg_title="Spieldatei wählen", dlg_exe="Programme",
        dlg_all="Alle Dateien",
    ),
    "ja": dict(
        start="フレームレートを解除", stop="停止", busy_btn="処理中…",
        retry="再試行", s_idle="待機", s_idle_sub="未起動", s_busy="処理中",
        s_busy_sub="ゲームプロセスを引き継ぎ中", s_ok="解除成功",
        s_ok_sub="有効 · {fps}", s_fail="解除失敗",
        s_fail_sub="ゲームプロセスを引き継げませんでした",
        stat_target="目標", stat_pid="プロセス", stat_patch="パッチ",
        patch_on="適用済み", patch_off="未適用",
        nav_skin="外観", nav_fps="フレームレート", nav_cfg="設定",
        nav_lang="言語", nav_about="バージョン情報",
        sub_skin="背景と配色を選択", sub_fps="起動時に書き込むフレームレート",
        sub_cfg="ゲームのインストール先と起動オプション",
        sub_lang="表示言語を選択", sub_about="バージョンと説明",
        appearance="外観", theme_light="ライト", theme_dark="ダーク",
        theme_auto="システムに従う", fps_target="目標フレームレート",
        unlimited="無制限", game_exe="ゲーム実行ファイル",
        auto_search="自動検索", imported="読み込み済み: {p}",
        not_imported="まだ読み込まれていません", searching="検索中…",
        found_import="見つかりました:\n{p}",
        not_found="見つかりません。YuanShen.exe を手動で選択してください",
        version="バージョン", updated="更新日", language="言語",
        err_no_exe="パスが無効です · 設定 · 設定 で YuanShen.exe を指定してください",
        err_fps="60〜1000 の整数を入力してください",
        err_admin="ゲームには管理者権限が必要です · 管理者として実行してください",
        err_access="ゲームプロセスを開けません · 管理者として実行してください",
        dlg_title="ゲーム実行ファイルを選択", dlg_exe="実行ファイル",
        dlg_all="すべてのファイル",
    ),
    "fr": dict(
        start="Débloquer la fréquence", stop="Arrêter", busy_btn="En cours…",
        retry="Réessayer", s_idle="En attente", s_idle_sub="Non démarré",
        s_busy="En cours", s_busy_sub="Prise en main du processus du jeu",
        s_ok="Débloqué", s_ok_sub="Actif · {fps}", s_fail="Échec",
        s_fail_sub="Impossible de prendre le processus du jeu",
        stat_target="Cible", stat_pid="Processus", stat_patch="Correctif",
        patch_on="Corrigé", patch_off="Non corrigé",
        nav_skin="Apparence", nav_fps="Fréquence", nav_cfg="Configuration",
        nav_lang="Langue", nav_about="À propos",
        sub_skin="Choisir le fond et les couleurs",
        sub_fps="Fréquence écrite au lancement",
        sub_cfg="Chemin d'installation et options de lancement",
        sub_lang="Choisir la langue de l'interface",
        sub_about="Version et informations",
        appearance="Apparence", theme_light="Clair", theme_dark="Sombre",
        theme_auto="Suivre le système", fps_target="Fréquence cible",
        unlimited="Illimité", game_exe="Exécutable du jeu",
        auto_search="Recherche auto", imported="Importé : {p}",
        not_imported="Aucun jeu importé", searching="Recherche…",
        found_import="Trouvé et importé :\n{p}",
        not_found="Introuvable. Sélectionnez YuanShen.exe manuellement",
        version="Version", updated="Mis à jour", language="Langue",
        err_no_exe="Chemin invalide · Indiquez YuanShen.exe dans Configuration",
        err_fps="Saisissez un entier entre 60 et 1000",
        err_admin="Le jeu nécessite des droits administrateur · Lancez l'outil en administrateur",
        err_access="Accès au processus refusé · Lancez l'outil en administrateur",
        dlg_title="Sélectionner l'exécutable du jeu", dlg_exe="Exécutables",
        dlg_all="Tous les fichiers",
    ),
    "ko": dict(
        start="프레임 제한 해제", stop="중지", busy_btn="처리 중…", retry="재시도",
        s_idle="대기 중", s_idle_sub="시작되지 않음", s_busy="처리 중",
        s_busy_sub="게임 프로세스 인계 중", s_ok="해제 성공",
        s_ok_sub="적용됨 · {fps}", s_fail="해제 실패",
        s_fail_sub="게임 프로세스를 인계하지 못했습니다",
        stat_target="목표", stat_pid="프로세스", stat_patch="패치",
        patch_on="적용됨", patch_off="미적용",
        nav_skin="스킨 설정", nav_fps="프레임 조정", nav_cfg="구성",
        nav_lang="언어", nav_about="정보",
        sub_skin="배경과 색상 선택", sub_fps="시작 시 기록할 목표 프레임",
        sub_cfg="게임 설치 경로 및 실행 옵션", sub_lang="인터페이스 언어 선택",
        sub_about="버전 및 설명",
        appearance="스킨", theme_light="라이트", theme_dark="다크",
        theme_auto="시스템 설정 따르기", fps_target="목표 프레임",
        unlimited="무제한", game_exe="게임 실행 파일", auto_search="자동 검색",
        imported="가져옴: {p}", not_imported="아직 가져온 게임이 없습니다",
        searching="검색 중…", found_import="찾아서 가져왔습니다:\n{p}",
        not_found="찾지 못했습니다. YuanShen.exe를 직접 선택하세요",
        version="버전", updated="업데이트", language="언어",
        err_no_exe="경로가 올바르지 않습니다 · 구성에서 YuanShen.exe를 지정하세요",
        err_fps="60–1000 사이의 정수를 입력하세요",
        err_admin="게임에 관리자 권한이 필요합니다 · 관리자 권한으로 실행하세요",
        err_access="게임 프로세스를 열 수 없습니다 · 관리자 권한으로 실행하세요",
        dlg_title="게임 실행 파일 선택", dlg_exe="실행 파일",
        dlg_all="모든 파일",
    ),
}

SETTINGS_TITLE = {"zh-CN": "设置", "zh-HK": "設定", "zh-TW": "設定",
                  "en": "Settings", "ru": "Настройки", "de": "Einstellungen",
                  "ja": "設定", "fr": "Réglages", "ko": "설정"}


DASH_EXTRA = {
    "zh-CN": ("仪表盘", "运行状态与解锁控制", "版本"),
    "zh-HK": ("儀表板", "執行狀態與解鎖控制", "版本"),
    "zh-TW": ("儀表板", "執行狀態與解鎖控制", "版本"),
    "en": ("Dashboard", "Status and unlock control", "Version"),
    "ru": ("Панель", "Состояние и управление", "Версия"),
    "de": ("Übersicht", "Status und Steuerung", "Version"),
    "ja": ("ダッシュボード", "状態と操作", "バージョン"),
    "fr": ("Tableau de bord", "État et contrôle", "Version"),
    "ko": ("대시보드", "상태 및 제어", "버전"),
}
_DASH_IDX = {"nav_dash": 0, "sub_dash": 1, "about_version_short": 2}


EXTRA = {
    "stat_path": {"zh-CN": "游戏路径", "zh-HK": "遊戲路徑", "zh-TW": "遊戲路徑",
                  "en": "Game path", "ru": "Путь к игре", "de": "Spielpfad",
                  "ja": "ゲームのパス", "fr": "Chemin du jeu", "ko": "게임 경로"},
    "stat_lang": {"zh-CN": "界面语言", "zh-HK": "介面語言", "zh-TW": "介面語言",
                  "en": "Interface language", "ru": "Язык интерфейса",
                  "de": "Sprache", "ja": "表示言語", "fr": "Langue",
                  "ko": "인터페이스 언어"},
    "hint_fps": {"zh-CN": "在「修改帧率」中调整", "zh-HK": "在「修改幀率」中調整",
                 "zh-TW": "在「修改幀率」中調整", "en": "Change it in Frame rate",
                 "ru": "Меняется в «Частота кадров»", "de": "Ändern unter Bildrate",
                 "ja": "「フレームレート」で変更", "fr": "Modifiable dans Fréquence",
                 "ko": "프레임 조정에서 변경"},
    "hint_patch": {"zh-CN": "运行时内存写入", "zh-HK": "執行時記憶體寫入",
                   "zh-TW": "執行時記憶體寫入", "en": "Written at runtime",
                   "ru": "Запись во время работы", "de": "Zur Laufzeit geschrieben",
                   "ja": "実行時に書き込み", "fr": "Écrit à l'exécution",
                   "ko": "실행 중 메모리 기록"},
    "hint_pid": {"zh-CN": "目标游戏进程 ID", "zh-HK": "目標遊戲進程 ID",
                 "zh-TW": "目標遊戲處理程序 ID", "en": "Target process ID",
                 "ru": "ID целевого процесса", "de": "Prozess-ID",
                 "ja": "対象プロセスの ID", "fr": "ID du processus cible",
                 "ko": "대상 프로세스 ID"},
    "minimize_opt": {"zh-CN": "启动后缩小", "zh-HK": "啟動後縮小",
                     "zh-TW": "啟動後縮小", "en": "Minimize after launch",
                     "ru": "Свернуть после запуска", "de": "Nach Start minimieren",
                     "ja": "起動後に最小化", "fr": "Réduire après lancement",
                     "ko": "실행 후 최소화"},
    "hint_start": {"zh-CN": "先退出游戏 · 再点此启动", "zh-HK": "先結束遊戲 · 再按此啟動",
                   "zh-TW": "先結束遊戲 · 再按此啟動", "en": "Quit the game first, then start",
                   "ru": "Сначала закройте игру", "de": "Erst Spiel beenden, dann starten",
                   "ja": "先にゲームを終了してから開始", "fr": "Quittez le jeu puis lancez",
                   "ko": "게임을 종료한 뒤 시작하세요"},
}


UI_KEYS = ("browse", "saved", "fps_hint", "custom_fps", "apply_fps", "minimize_hint")
UI_TEXT = {
    "zh-CN": ("选择文件", "设置自动保存", "更改将在下次启动或解锁时生效", "自定义帧率", "应用", "启动游戏后，自动最小化此窗口"),
    "zh-HK": ("選擇檔案", "設定自動儲存", "變更會在下次啟動或解鎖時生效", "自訂幀率", "套用", "啟動遊戲後，自動最小化此視窗"),
    "zh-TW": ("選擇檔案", "設定自動儲存", "變更會在下次啟動或解鎖時生效", "自訂幀率", "套用", "啟動遊戲後，自動最小化此視窗"),
    "en": ("Browse", "Settings saved automatically", "Changes apply on the next launch or unlock", "Custom frame rate", "Apply", "Minimize this window after launching the game"),
    "ru": ("Выбрать файл", "Настройки сохраняются автоматически", "Изменения применятся при следующем запуске", "Своя частота кадров", "Применить", "Свернуть окно после запуска игры"),
    "de": ("Durchsuchen", "Einstellungen werden automatisch gespeichert", "Änderungen gelten beim nächsten Start", "Eigene Bildrate", "Anwenden", "Dieses Fenster nach dem Spielstart minimieren"),
    "ja": ("ファイルを選択", "設定は自動保存されます", "変更は次回の起動・解除時に適用されます", "カスタムフレームレート", "適用", "ゲーム起動後にこのウィンドウを最小化"),
    "fr": ("Parcourir", "Enregistrement automatique", "Appliqué au prochain lancement ou déblocage", "Fréquence personnalisée", "Appliquer", "Réduire cette fenêtre après le lancement du jeu"),
    "ko": ("파일 선택", "설정이 자동으로 저장됩니다", "변경 사항은 다음 실행 또는 해제 시 적용됩니다", "사용자 지정 프레임", "적용", "게임 실행 후 이 창을 최소화합니다"),
}

STAT_STATE = {'zh-CN': '状态', 'zh-HK': '狀態', 'zh-TW': '狀態', 'en': 'Status', 'ru': 'Состояние', 'de': 'Status', 'ja': '状態', 'fr': 'État', 'ko': '상태'}

PANE_KEYS = ("nav_dash", "nav_skin", "nav_fps", "nav_cfg", "nav_lang", "nav_about")
SUB_KEYS = ("sub_dash", "sub_skin", "sub_fps", "sub_cfg", "sub_lang", "sub_about")
ICONS = ("dash", "skin", "fps", "cfg", "lang", "about")


def apply_palette(name):
    global BG, CARD, HOVER, TEXT, SUB, MUTED, LINE, TRACK, SEL_BG
    global DROP_BG, DROP_HOVER, PLACE, GLOW, TINT, SIDE, SIDE_LINE
    global BLUE, BLUE_HI, GREEN, GREEN_TX, RED, RED_TX, RED_FILL, RED_FILL_HI
    pal = THEMES.get(name, THEMES["light"])
    for k, v in pal.items():
        globals()[k] = v
    SIDE = pal.get("SIDE", pal["BG"])
    SIDE_LINE = pal.get("SIDE_LINE", pal["LINE"])
    DROP_BG = pal["DROP_BG"]
    DROP_HOVER = pal["DROP_HOVER"]


def hex2rgb(h):
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def mix(c1, c2, t):
    a, b = hex2rgb(c1), hex2rgb(c2)
    t = 0.0 if t < 0 else (1.0 if t > 1 else t)
    return "#%02x%02x%02x" % (int(a[0] + (b[0] - a[0]) * t),
                              int(a[1] + (b[1] - a[1]) * t),
                              int(a[2] + (b[2] - a[2]) * t))


def motion_clamp(value, low=0.0, high=1.0):
    return max(low, min(high, float(value)))


def motion_rgb(colour):
    if isinstance(colour, (tuple, list)):
        return tuple(int(v) for v in colour[:3])
    value = colour.lstrip('#')
    if len(value) == 3:
        value = ''.join(c * 2 for c in value)
    return tuple(int(value[i:i+2], 16) for i in (0, 2, 4))


def motion_mix(first, second, amount):
    a, b = motion_rgb(first), motion_rgb(second)
    t = motion_clamp(amount)
    return tuple(round(x+(y-x)*t) for x, y in zip(a, b))


def motion_cookie9_points():
    """Sample Material cookie9Sided from material_shapes 1.0.0, 8 per segment.

    https://github.com/ulims/material_shapes/blob/main/lib/src/material_shapes.dart
    """
    segments = (
        ((.828816587, -.188677999), (.925931926, -.081637676),
         (.925931926, .081637676), (.828816587, .188677999)),
        ((.828816587, .188677999), (.779422153, .243120441),
         (.753346816, .314761840), (.756190221, .388217301)),
    )
    points = []
    denominator = 1.8520823466029928
    for sector in range(9):
        angle = sector*2*math.pi/9
        cosine, sine = math.cos(angle), math.sin(angle)
        for a, b, c, d in segments:
            for sample in range(8):
                t = sample/8.0
                q = 1-t
                x = q*q*q*a[0]+3*q*q*t*b[0]+3*q*t*t*c[0]+t*t*t*d[0]
                y = q*q*q*a[1]+3*q*q*t*b[1]+3*q*t*t*c[1]+t*t*t*d[1]
                # Rotate the repeated sectors, then apply the official -90°
                # orientation and square normalization. Keep the source's
                # slight Y normalization offset rather than inventing one.
                rotated_x = x*cosine-y*sine
                rotated_y = x*sine+y*cosine
                points.append(((rotated_y+.9260411733014965)/denominator,
                               (-rotated_x+.9278611550627665)/denominator))
    return tuple(points)


MOTION_COOKIE9_POINTS = motion_cookie9_points()


def motion_cookie_outline(morph=1.0):
    """Shared centred outline for the action and its enlarged background."""
    morph = motion_clamp(morph, -0.05, 1.15)
    turn = morph*2*math.pi/9
    cosine, sine = math.cos(turn), math.sin(turn)
    points = []
    for nx, ny in MOTION_COOKIE9_POINTS:
        dx, dy = nx-.5, ny-.5
        angle = math.atan2(dy, dx)
        x = .5*math.cos(angle)*(1-morph)+dx*morph
        y = .5*math.sin(angle)*(1-morph)+dy*morph
        points.append((x*cosine-y*sine, x*sine+y*cosine))
    return tuple(points)


def flower_button(diameter=80, scale=1.0, hover=0.0, press=0.0,
                  phase=0.0, active=False, mode='play', accent='#3d86ff',
                  dark=True, samples=3, morph=1.0, glyph_progress=None):
    """Return the reference-style blue, nine-lobed cookie action button.

    ``diameter`` is the full flower diameter in logical pixels; the returned
    image adds 22% of that diameter as a transparent glow margin on each side.
    Centre the *whole* returned image on the action location. ``press`` runs
    from 0 (released) to 1 (pressed); ``hover`` is the interpolated hover value.
    ``phase`` is radians, suitable for a restrained slow idle glow. Only the
    glow changes while idle: the silhouette and glyph do not rotate.

    ``morph`` is 0 for a circle and 1 for the official MaterialShapes.cookie9Sided
    cubic outline. A small overshoot to 1.15 is permitted for an easeOutBack transition.
    ``glyph_progress`` animates a split triangle (0) into two round pause bars
    (1), without rotating the glyph. Omit it to follow ``mode``.

    Modes: play, pause, busy, retry. ``busy`` shows a short arc, not a spinning
    play/pause glyph. The arc can rotate by passing the animation phase.
    """
    diameter = max(24.0, float(diameter))
    scale = max(0.25, float(scale))
    ss = max(2, int(samples))
    hover, press = motion_clamp(hover), motion_clamp(press)
    morph = motion_clamp(morph, -0.05, 1.15)
    margin = max(12.0, math.ceil(diameter*0.22))
    logical_size = diameter+2*margin
    out_size = max(1, round(logical_size*scale))
    draw_size = out_size*ss
    unit = draw_size/logical_size
    centre = logical_size/2
    # A settled, subtly elastic press is driven by the caller; no geometry
    # travels beyond 2.4% on hover or 4.5% on press.
    zoom = 1.0 + 0.024*hover - 0.045*press
    radius = diameter*0.5*zoom
    cy = centre + 0.7*press
    image = Image.new('RGBA', (draw_size, draw_size))
    tint = motion_rgb(accent)
    pulse = (0.5+0.5*math.sin(float(phase)))*float(bool(active))

    # Nested ellipses make a soft, low-opacity penumbra without ImageFilter.
    # Each inner fill replaces the previous alpha to form a continuous ramp.
    shadow = Image.new('RGBA', image.size)
    draw = ImageDraw.Draw(shadow)
    shadow_offset = diameter*(0.045-0.018*press)
    for index in range(26):
        t = index/25.0
        rx = radius*(1.22-0.25*t)
        ry = radius*(0.98-0.18*t)
        alpha = round((7 if dark else 3) + (16 if dark else 9)*t*t)
        draw.ellipse(((centre-rx)*unit, (cy+shadow_offset-ry)*unit,
                      (centre+rx)*unit, (cy+shadow_offset+ry)*unit),
                     fill=(0, 0, 0, alpha))
    image = Image.alpha_composite(image, shadow)

    glow = Image.new('RGBA', image.size)
    draw = ImageDraw.Draw(glow)
    strength = (18 if dark else 9) + hover*10 + pulse*3
    for index in range(32):
        t = index/31.0
        r = radius + margin*(0.90-0.92*t)
        alpha = round(strength*t*t*(1.0-0.30*press))
        draw.ellipse(((centre-r)*unit, (cy-r)*unit,
                      (centre+r)*unit, (cy+r)*unit), fill=tint+(alpha,))
    image = Image.alpha_composite(image, glow)

    draw = ImageDraw.Draw(image)
    points = []
    # The shape turns exactly one 40° symmetry sector during a state morph.
    # At both settled endpoints it is stationary and the pause/play glyph is
    # drawn separately, so the glyph never spins with the cookie outline.
    for x, y in motion_cookie_outline(morph):
        points.append(((centre+diameter*zoom*x)*unit,
                       (cy+diameter*zoom*y)*unit))
    fill = motion_mix(tint, '#ffffff', 0.045*hover)
    if press:
        fill = motion_mix(fill, '#173d80', 0.045*press)
    draw.polygon(points, fill=fill+(255,))

    icon = (255, 255, 255, 255)
    glyph_unit = diameter*zoom
    bar = max(2.0, glyph_unit*0.055)
    half_height = glyph_unit*0.093
    gap = glyph_unit*0.060

    def capsule(x1, y1, x2, y2, width):
        width_px = max(1, round(width*unit))
        draw.line((x1*unit, y1*unit, x2*unit, y2*unit), fill=icon,
                  width=width_px)
        r = width*unit/2
        for x, y in ((x1, y1), (x2, y2)):
            xx, yy = x*unit, y*unit
            draw.ellipse((xx-r, yy-r, xx+r, yy+r), fill=icon)

    if mode == 'busy':
        r = glyph_unit*0.13
        box = ((centre-r)*unit, (cy-r)*unit, (centre+r)*unit, (cy+r)*unit)
        start = math.degrees(float(phase)) % 360
        draw.arc(box, start=start, end=start+245, fill=icon,
                 width=max(2, round(glyph_unit*0.045*unit)))
        rr = glyph_unit*0.0225*unit
        for angle in (start, start+245):
            angle = math.radians(angle)
            x = (centre+r*math.cos(angle))*unit
            y = (cy+r*math.sin(angle))*unit
            draw.ellipse((x-rr, y-rr, x+rr, y+rr), fill=icon)
    elif mode == 'retry':
        r = glyph_unit*0.125
        box = ((centre-r)*unit, (cy-r)*unit, (centre+r)*unit, (cy+r)*unit)
        draw.arc(box, start=30, end=315, fill=icon,
                 width=max(2, round(glyph_unit*0.045*unit)))
        x = centre+r*math.cos(math.radians(315))
        y = cy+r*math.sin(math.radians(315))
        points = ((x+glyph_unit*0.035, y-glyph_unit*0.050),
                  (x+glyph_unit*0.045, y+glyph_unit*0.040),
                  (x-glyph_unit*0.040, y+glyph_unit*0.010))
        draw.polygon([(x*unit, y*unit) for x, y in points], fill=icon)
    else:
        # Split the play triangle into two touching polygons. The left and
        # right pieces interpolate to the two pause bars as in play_pause.
        # This gives a continuous morph with no glyph rotation or crossfade.
        progress = motion_clamp((1.0 if mode == 'pause' else 0.0)
                                if glyph_progress is None else glyph_progress)
        left = centre-glyph_unit*0.055
        tip = centre+glyph_unit*0.115
        split = (left+tip)/2
        top, bottom = cy-glyph_unit*0.106, cy+glyph_unit*0.106
        play = (((left, top), (split, (top+cy)/2),
                 (split, (bottom+cy)/2), (left, bottom)),
                ((split, (top+cy)/2), (tip, cy),
                 (tip, cy), (split, (bottom+cy)/2)))
        for index, start_points in enumerate(play):
            x = centre + (-gap if index == 0 else gap)
            # Both polygons collapse to centre lines at pause. The growing
            # rounded stroke supplies the final pill-shaped bars.
            end_height = glyph_unit*0.080
            end_points = ((x, cy-end_height), (x, cy-end_height),
                          (x, cy+end_height), (x, cy+end_height))
            points = tuple((a[0]+(b[0]-a[0])*progress,
                            a[1]+(b[1]-a[1])*progress)
                           for a, b in zip(start_points, end_points))
            draw.polygon([(x*unit, y*unit) for x, y in points], fill=icon)
            for a, b in zip(points, points[1:]+points[:1]):
                capsule(*a, *b, glyph_unit*(0.034+0.021*progress))

    return image.resize((out_size, out_size), Image.Resampling.LANCZOS)


def flower_status_card(width=524, height=286, scale=1.0,
                   dark=True, base=None, wave=None, radius=18, outline=None,
                   samples=2):
    """Clip an enlarged copy of the action's nine-lobed outline to the card.

    Preserve the action's orientation and aspect ratio. The calm background
    is rendered once per page/theme, keeping animation frames inexpensive.
    """
    width, height = max(40.0, float(width)), max(40.0, float(height))
    scale = max(0.25, float(scale))
    ss = max(1, int(samples))
    out_w, out_h = max(1, round(width*scale)), max(1, round(height*scale))
    draw_w, draw_h = out_w*ss, out_h*ss
    sx, sy = draw_w/width, draw_h/height
    base = motion_rgb(base or ('#252628' if dark else '#ffffff'))
    wave = motion_rgb(wave or ('#283244' if dark else '#edf3fe'))
    image = Image.new('RGBA', (draw_w, draw_h), base+(255,))
    draw = ImageDraw.Draw(image)
    # The action centre is (445, 222) on a card starting at (26, 90).
    # Scale the same silhouette uniformly; no independent wave or distortion.
    cx, cy = width*(419/524), height*(132/286)
    diameter = height*1.20
    points = [((cx+diameter*x)*sx, (cy+diameter*y)*sy)
              for x, y in motion_cookie_outline()]
    # Extend the right field to the card edge, preserving the flower's left
    # contour while filling the lower-right corner outside its silhouette.
    draw.rectangle((cx*sx, 0, draw_w, draw_h), fill=wave+(255,))
    draw.polygon(points, fill=wave+(255,))
    mask = Image.new('L', (draw_w, draw_h), 0)
    mask_draw = ImageDraw.Draw(mask)
    rr = max(0, round(min(radius, width/2, height/2)*min(sx, sy)))
    mask_draw.rounded_rectangle((0, 0, draw_w-1, draw_h-1), radius=rr, fill=255)
    image.putalpha(mask)
    if outline:
        draw = ImageDraw.Draw(image)
        inset = max(1, round(scale*ss/2))
        draw.rounded_rectangle((inset, inset, draw_w-1-inset, draw_h-1-inset),
                               radius=max(0, rr-inset), outline=motion_rgb(outline)+(255,),
                               width=max(1, round(scale*ss)))
    return image.resize((out_w, out_h), Image.Resampling.LANCZOS)



# Timing and curves match FlClash v0.9.2 lib/ui/sidebar.dart.
SIDEBAR_SWITCH_SECONDS = 0.320
SIDEBAR_ICON_SECONDS = 0.350
SIDEBAR_EXPAND_SECONDS = 0.250
BUTTON_MORPH_SECONDS = 0.450


def bezier_ease(value, x1, y1, x2, y2):
    """Evaluate a Flutter/CSS cubic by solving its x coordinate first."""
    x = max(0.0, min(1.0, float(value)))
    if x == 0.0 or x == 1.0:
        return x
    low, high = 0.0, 1.0
    for _ in range(18):
        t = (low+high)/2
        mt = 1-t
        current = 3*mt*mt*t*x1 + 3*mt*t*t*x2 + t*t*t
        if current < x:
            low = t
        else:
            high = t
    t = (low+high)/2
    return 3*(1-t)*(1-t)*t*y1 + 3*(1-t)*t*t*y2 + t*t*t


class Spring:
    __slots__ = ("value", "target", "vel", "k", "d")

    def __init__(self, value=0.0, k=260.0, d=22.0):
        self.value = float(value)
        self.target = float(value)
        self.vel = 0.0
        self.k = k
        self.d = d

    def set(self, target):
        self.target = float(target)

    def snap(self, value):
        self.value = self.target = float(value)
        self.vel = 0.0

    def update(self, dt):
        a = (self.target - self.value) * self.k - self.vel * self.d
        self.vel += a * dt
        self.value += self.vel * dt
        return self.value


def _dpi_scale():
    try:
        hdc = ctypes.windll.user32.GetDC(0)
        dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)
        ctypes.windll.user32.ReleaseDC(0, hdc)
        if dpi:
            return dpi / 96.0
    except Exception:
        pass
    return 1.0


def _system_is_dark():
    try:
        import winreg
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                           r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
        v, _ = winreg.QueryValueEx(k, "AppsUseLightTheme")
        return int(v) == 0
    except Exception:
        return True


def _config_path():
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    d = os.path.join(base, "GenshinUnlocker")
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    return os.path.join(d, "settings.json")


class App:
    def __init__(self, root):
        self.root = root
        self.number_font = str(root.tk.call("font", "actual", "TkDefaultFont", "-family"))
        self.nav_started = -1e9
        self._nav_from = self._nav_target = (122.0, 138.0)
        self._nav_fill_from = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self._nav_pop_started = [-1e9]*6
        self._hover_started = -1e9
        self._hover_from = [0.0]*6
        self._side_started = -1e9
        self._side_from = self._side_to = float(SIDE_W)
        self.btn_pressed = False
        self._button_hover_started = -1e9
        self._button_hover_from = 0.0
        self._morph_started = -1e9
        self._morph_from = self._morph_to = 1.0
        self._glyph_from = self._glyph_to = 0.0
        self._status_started = -1e9
        self._status_from = None
        self._button_frames = {}
        self._button_photo = None
        self._button_key = None
        self._status_render_key = None
        self._wave_photo = None
        self._sidebar_animation_dirty = False
        self.S = min(max(1.0, _dpi_scale()),
                     max(0.65, (root.winfo_screenwidth() - 48) / W),
                     max(0.65, (root.winfo_screenheight() - 100) / H))
        self.q = queue.Queue()
        self.unlocker = None
        self.state = "idle"
        self.detail = ""
        self.target_fps = 144
        self.active_fps = None
        self.history = []
        self.info = {"target": "144 FPS", "pid": "\u2014", "patch": "\u2014"}
        self.path_var = tk.StringVar()
        self.fps_var = tk.StringVar(value="144")

        self.phase = 0.0
        self.pulse = 0.0
        self.progress = Spring(0.0, 90.0, 16.0)
        self.btn_scale = Spring(1.0, 330.0, 21.0)
        self.btn_hover = 0.0
        self.btn_hover_t = 0.0
        self.side_w = Spring(SIDE_W, 260.0, 24.0)
        self.page_dx = Spring(0.0, 220.0, 20.0)
        self.btn_mode = "start"
        self.btn_label = ""
        self._fx = []
        self._ring_key = None
        self._ring_photo = None
        self._t_last = time.perf_counter()
        self.page = 0
        self.collapsed = False
        self.hover_item = -1
        self.sl_x = None
        self.sl_drag = False
        self.sl_cv = None
        self.drop_open = False
        self.drop_cv = None
        self.cfg_status = None
        self.ring_item = None

        cfg = self._load_cfg()
        self.theme_mode = cfg.get("theme", "auto")
        if self.theme_mode not in ("light", "dark", "auto"):
            self.theme_mode = "auto"
        self.lang = cfg.get("lang", "zh-CN")
        if self.lang not in dict(LANGS):
            self.lang = "zh-CN"
        try:
            self.target_fps = max(60, min(1000, int(cfg.get("fps", 144))))
        except (ValueError, TypeError, OverflowError):
            self.target_fps = 144
        self.fps_var.set(str(self.target_fps))
        self.info["target"] = self._fps_label()
        self.path_var.set(str(cfg.get("path", "") or ""))
        self.collapsed = bool(cfg.get("collapsed", False))
        self.minimize = bool(cfg.get("minimize", False))
        self._resolved = self._resolve_theme()
        apply_palette(self._resolved)
        if self.collapsed:
            self.side_w.snap(SIDE_MINI)
        self._side_from = self._side_to = self.side_w.value

        self._autodetect()
        self._build()
        self.path_var.trace_add("write", self._path_changed)
        self.root.after(16, self._tick)
        self.root.after(60, self._pump)
        self.root.after(500, self._watch)
        self._apply("idle", "")

    # ------------------------------------------------------------ 文案
    def t(self, key, **kw):
        if key in UI_KEYS:
            return UI_TEXT.get(self.lang, UI_TEXT["zh-CN"])[UI_KEYS.index(key)]
        if key == "stat_state":
            return STAT_STATE.get(self.lang, STAT_STATE["zh-CN"])
        if key in EXTRA:
            row = EXTRA[key]
            return row.get(self.lang, row["zh-CN"])
        if key in _DASH_IDX:
            row = DASH_EXTRA.get(self.lang, DASH_EXTRA["zh-CN"])
            return row[_DASH_IDX[key]]
        d = T.get(self.lang) or T["zh-CN"]
        s = d.get(key) or T["zh-CN"].get(key, key)
        return s.format(**kw) if kw else s

    def _fps_label(self, v=None):
        v = self.target_fps if v is None else v
        return "\u221e" if v >= 1000 else "%d FPS" % v

    # ------------------------------------------------------------ 配置
    def _load_cfg(self):
        try:
            with open(_config_path(), "r", encoding="utf-8") as f:
                cfg = json.load(f)
                return cfg if isinstance(cfg, dict) else {}
        except Exception:
            return {}

    def _save_cfg(self):
        try:
            with open(_config_path(), "w", encoding="utf-8") as f:
                json.dump({"theme": self.theme_mode, "lang": self.lang,
                           "collapsed": self.collapsed,
                           "minimize": self.minimize,
                           "fps": self.target_fps,
                           "path": self.path_var.get().strip()}, f,
                          ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _resolve_theme(self):
        if self.theme_mode == "auto":
            return "dark" if _system_is_dark() else "light"
        return self.theme_mode

    def _set_theme(self, mode):
        self.theme_mode = mode
        self._resolved = self._resolve_theme()
        apply_palette(self._resolved)
        self._save_cfg()
        self._rebuild_ui()

    def _set_lang(self, lang):
        patched = self.info.get("patch") == self.t("patch_on")
        had_patch = self.info.get("patch") in (self.t("patch_on"), self.t("patch_off"))
        self.lang = lang
        self.btn_label = self.t({"idle": "start", "busy": "busy_btn", "ok": "stop", "fail": "retry"}[self.state])
        if had_patch:
            self.info["patch"] = self.t("patch_on" if patched else "patch_off")
        self._save_cfg()
        self._rebuild_ui()

    # ------------------------------------------------------------ 工具
    def px(self, v):
        return int(round(v * self.S))

    def f(self, size, weight="normal", mono=False):
        return (self.number_font if mono else FONT, -self.px(size), weight)

    @staticmethod
    def _rr_pts(x1, y1, x2, y2, r):
        r = max(0.0, min(r, (x2 - x1) / 2.0, (y2 - y1) / 2.0))
        points = []
        for cx, cy, start in ((x2-r, y1+r, -90), (x2-r, y2-r, 0),
                              (x1+r, y2-r, 90), (x1+r, y1+r, 180)):
            for step in range(9):
                angle = math.radians(start + step*90/8)
                points.extend((cx + r*math.cos(angle), cy + r*math.sin(angle)))
        return points

    def _rr(self, c, x1, y1, x2, y2, r, **kw):
        return c.create_polygon(self._rr_pts(x1, y1, x2, y2, r), smooth=True, **kw)

    def _res(self, name):
        base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base, name)

    # ------------------------------------------------------------ 构建
    def _build(self):
        r = self.root
        r.title("原神帧率解锁 · " + VERSION if self.lang == "zh-CN" else "Genshin FPS Unlocker · " + VERSION)
        r.configure(bg=BG)
        r.resizable(False, False)
        w, h = self.px(W), self.px(H)
        sw, sh = r.winfo_screenwidth(), r.winfo_screenheight()
        r.geometry("%dx%d+%d+%d" % (w, h, max(0, (sw-w)//2), max(0, (sh-h)//2-20)))
        try:
            r.iconbitmap(self._res("icon.ico"))
        except Exception:
            pass
        side_width = self.px(self.side_w.value)
        # Keep every backing size fixed. The main frame moves above the rail
        # to occlude its unused portion, without resizing a Canvas or its parent.
        self.side_clip=tk.Frame(r,bg=SIDE,highlightthickness=0,bd=0)
        self.side_clip.place(x=0,y=0,width=self.px(SIDE_W),height=h)
        self.side = tk.Canvas(self.side_clip, bg=SIDE, highlightthickness=0, bd=0, takefocus=1)
        self.side.place(x=0,y=0,width=self.px(SIDE_W),height=h)
        self._side_items={}
        self._side_item_values={}
        self.side.bind("<Button-1>", self._side_click)
        self.side.bind("<Motion>", self._side_motion)
        self.side.bind("<Leave>", lambda e: self._side_motion(None))
        self.side.bind("<Up>", lambda e: self._nav_key(-1))
        self.side.bind("<Down>", lambda e: self._nav_key(1))
        self.side.bind("<Left>", lambda e: self._toggle_side() if not self.collapsed else None)
        self.side.bind("<Right>", lambda e: self._toggle_side() if self.collapsed else None)
        self.main = tk.Frame(r, bg=BG, highlightthickness=0)
        self.main.place(x=side_width,y=0,width=w,height=h)
        self.content = tk.Frame(self.main, bg=BG, highlightthickness=0)
        self.content.place(x=self.px((SIDE_W-self.side_w.value)/2),y=0,
                           width=self.px(W-SIDE_W),height=h)
        self.cv = tk.Canvas(self.content, bg=BG, highlightthickness=0, bd=0)
        self.cv.place(x=0, y=0, width=self.px(W-SIDE_W), height=h)
        self.pane_body = tk.Frame(self.content, bg=CARD, highlightthickness=0)
        self._draw_side()
        self._render_page()
        r.bind("<Escape>", lambda e: self._close_drop())
        r.bind("<Button-1>", self._outside_drop)
        r.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.after(30, self._apply_title_bar)

    def _nav_key(self, delta):
        self._go((self.page + delta) % len(PANE_KEYS))
        return "break"

    def _outside_drop(self, event):
        if self.drop_open and event.widget not in (self.sel_cv, self.drop_cv):
            self._close_drop()

    def _apply_title_bar(self):
        try:
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            dark = ctypes.c_int(1 if self._resolved == "dark" else 0)
            for attr in (20, 19):
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, ctypes.c_int(attr), ctypes.byref(dark),
                    ctypes.sizeof(dark))
        except Exception:
            pass

    def _rebuild_ui(self):
        x, y = self.root.winfo_x(), self.root.winfo_y()
        self._ring_key = None
        self._ring_photo = None
        self.ring_item = None
        self._fx = []
        self._button_frames.clear()
        self._button_photo=None
        self._button_key=None
        self._status_from=None
        self.root.configure(bg=BG)
        self.side_clip.destroy()
        self.main.destroy()
        self._build()
        self.root.geometry("+%d+%d" % (x, y))
        self._refresh_stats()
        self.root.lift()
        self.root.after(30, self._apply_title_bar)

    # ------------------------------------------------------------ 侧栏
    def _icon(self,c,name,cx,cy,s,color,fill_progress=0.0,cache_key=None):
        w=max(1,int(round((1.6+0.3*fill_progress)*self.S)))
        detail=mix(color,SIDE,fill_progress)
        part=0
        def draw(kind,*coords,**style):
            nonlocal part
            key="%s_%d"%(cache_key,part)
            part+=1
            if cache_key is not None:
                return self._side_primitive(kind,key,coords,style)
            return getattr(c,"create_"+kind)(*coords,**style)
        r=s/2.0
        if name=="dash":
            draw("oval",cx-r,cy-r,cx+r,cy+r,outline=color,width=w,fill=mix(SIDE,color,fill_progress))
            dot=1.6*self.S
            draw("oval",cx-dot,cy-dot,cx+dot,cy+dot,fill=detail,outline="")
        elif name=="skin":
            draw("oval",cx-r,cy-r,cx+r,cy+r,outline=color,width=w,fill=mix(SIDE,color,fill_progress))
            draw("line",cx-r+1,cy,cx+r-1,cy,fill=detail,width=w)
            draw("line",cx,cy-r+1,cx,cy+r-1,fill=detail,width=w)
        elif name=="fps":
            # Canvas Y increases downward: 225 -> 315 degrees sweeps
            # clockwise from upper-left, through up, to upper-right.
            draw("arc",cx-r,cy-r,cx+r,cy+r,start=200,extent=140,style="arc",outline=color,width=w)
            angle=math.pi*1.25+math.pi*0.5*motion_clamp(fill_progress)
            length=r*0.70
            draw("line",cx,cy,cx+length*math.cos(angle),cy+length*math.sin(angle),
                 fill=color,width=w,capstyle="round",tags=("fps_needle",))
        elif name=="cfg":
            draw("polygon",cx-s/2,cy-s*.28,cx-s*.12,cy-s*.28,cx,cy-s*.42,
                 cx+s/2,cy-s*.42,cx+s/2,cy+s*.34,cx-s/2,cy+s*.34,
                 smooth=True,outline=color,fill=mix(SIDE,color,fill_progress),width=w)
        elif name=="lang":
            draw("oval",cx-r,cy-r,cx+r,cy+r,outline=color,width=w,fill=mix(SIDE,color,fill_progress))
            draw("line",cx-r,cy,cx+r,cy,fill=detail,width=w)
            draw("oval",cx-r*.45,cy-r,cx+r*.45,cy+r,outline=detail,width=w)
        else:
            draw("oval",cx-r,cy-r,cx+r,cy+r,outline=color,width=w,fill=mix(SIDE,color,fill_progress))
            draw("line",cx,cy-r*.15,cx,cy+r*.5,fill=detail,width=w)
            dot=1.4*self.S
            draw("oval",cx-dot,cy-r*.55,cx+dot,cy-r*.55+2*dot,fill=detail,outline="")

    def _side_primitive(self,kind,key,coords,style):
        """Update retained rail items; settled properties never enter Tcl again."""
        coords=tuple(coords)
        item=self._side_items.get(key)
        if item is None:
            item=getattr(self.side,"create_"+kind)(*coords,**style)
            self._side_items[key]=item
        else:
            previous_coords,previous_style=self._side_item_values[key]
            if coords!=previous_coords:
                self.side.coords(item,*coords)
            changes={name:value for name,value in style.items() if previous_style.get(name)!=value}
            if changes:
                self.side.itemconfig(item,**changes)
        self._side_item_values[key]=(coords,dict(style))
        return item

    def _item_rect(self, i):
        return self.px(12), self.px(108 + i*52), self.px(10)

    def _draw_side(self):
        now=time.perf_counter()
        w,h=self.px(self.side_w.value),self.px(H)
        expansion=motion_clamp((self.side_w.value-SIDE_MINI)/(SIDE_W-SIDE_MINI))
        alpha=motion_clamp((expansion-0.4)/0.6)
        label_state="normal" if alpha>0.001 else "hidden"
        def draw(kind,key,*coords,**style):
            return self._side_primitive(kind,key,coords,style)
        def rounded(key,x1,y1,x2,y2,r,**style):
            return draw("polygon",key,*self._rr_pts(x1,y1,x2,y2,r),smooth=True,**style)
        draw("line","edge",w-1,0,w-1,h,fill=SIDE_LINE)
        cx,cy=self.px(33),self.px(39)
        rounded("brand_tile",cx-self.px(17),cy-self.px(17),cx+self.px(17),cy+self.px(17),
                self.px(10),fill=BLUE,outline="")
        r=self.px(10)
        draw("arc","brand_arc",cx-r,cy-r,cx+r,cy+r,start=-40,extent=260,style="arc",outline="#ffffff",width=self.px(2))
        draw("line","brand_needle",cx,cy,cx+self.px(5),cy-self.px(6),fill="#ffffff",width=self.px(2),capstyle="round")
        draw("oval","brand_dot",cx-self.px(2),cy-self.px(2),cx+self.px(2),cy+self.px(2),fill="#ffffff",outline="")
        draw("text","brand_title",self.px(60),self.px(32),text="GENSHIN",anchor="w",fill=mix(SIDE,TEXT,alpha),
             font=self.f(15,"bold",mono=True),state=label_state)
        draw("text","brand_caption",self.px(60),self.px(51),text="FPS UNLOCKER",anchor="w",fill=mix(SIDE,MUTED,alpha),
             font=self.f(9,mono=True),state=label_state)
        draw("line","header_divider",self.px(16),self.px(83),w-self.px(16),self.px(83),fill=SIDE_LINE)
        fills,hovers=self._nav_fill_values(now),self._side_hover_values(now)
        for i,key in enumerate(PANE_KEYS):
            x,y,rad=self._item_rect(i)
            selected=i==self.page
            background=self._sel_fill() if selected else mix(SIDE,TEXT,0.04*hovers[i])
            rounded("nav_surface_%d"%i,x,y,w-self.px(12),y+self.px(44),rad,
                    fill=background,outline="",state="normal" if selected or hovers[i]>0.002 else "hidden")
            p=motion_clamp((now-self._nav_pop_started[i])/SIDEBAR_ICON_SECONDS)
            scale=1.0 if ICONS[i]=="fps" else 1+0.10*math.sin(math.pi*p)
            color=mix(SUB,TEXT,fills[i])
            self._icon(self.side,ICONS[i],self.px(33),y+self.px(22),self.px(20)*scale,color,fills[i],"nav_icon_%d"%i)
            draw("text","nav_text_%d"%i,self.px(58),y+self.px(22),anchor="w",text=self.t(key),
                 fill=mix(SIDE,color,alpha),font=self.f(13,"bold" if selected else "normal"),
                 width=self.px(SIDE_W-70),state=label_state)
        top,bottom=self._nav_marker_bounds(now)
        self.nav_indicator=rounded("indicator",self.px(12),self.px(top),self.px(15),self.px(bottom),self.px(1.5),
                                   fill=BLUE,outline="",tags=("nav_indicator",))
        draw("line","footer_divider",self.px(16),h-self.px(76),w-self.px(16),h-self.px(76),fill=SIDE_LINE)
        bx,by=self.px(16),h-self.px(57)
        rounded("toggle_surface",bx,by,bx+self.px(34),by+self.px(34),self.px(8),fill=HOVER,outline="")
        draw("rectangle","toggle_frame",bx+self.px(9),by+self.px(10),bx+self.px(25),by+self.px(24),
             outline=SUB,width=max(1,self.px(1.2)))
        draw("line","toggle_separator",bx+self.px(15),by+self.px(10),bx+self.px(15),by+self.px(24),fill=SUB)
        draw("text","version",w-self.px(18),by+self.px(17),anchor="e",text=VERSION,
             fill=mix(SIDE,MUTED,alpha),font=self.f(11,mono=True),state=label_state)

    def _nav_marker_bounds(self, now=None):
        now = time.perf_counter() if now is None else now
        t = motion_clamp((now-self.nav_started)/SIDEBAR_SWITCH_SECONDS)
        lead = bezier_ease(min(1.0,t/0.6),0.215,0.61,0.355,1.0)
        trail = bezier_ease(max(0.0,(t-0.35)/0.65),0.645,0.045,0.355,1.0)
        a,b = self._nav_from
        x,y = self._nav_target
        downward = (x+y) >= (a+b)
        top = a+(x-a)*(trail if downward else lead)
        bottom = b+(y-b)*(lead if downward else trail)
        if bottom-top < 16:
            centre = (top+bottom)/2
            top,bottom = centre-8,centre+8
        return top,bottom

    def _nav_fill_values(self, now=None):
        now = time.perf_counter() if now is None else now
        p = bezier_ease((now-self.nav_started)/SIDEBAR_ICON_SECONDS,0.645,0.045,0.355,1.0)
        return [v+((1.0 if i==self.page else 0.0)-v)*p for i,v in enumerate(self._nav_fill_from)]

    def _side_hover_values(self, now=None):
        now = time.perf_counter() if now is None else now
        p = motion_clamp((now-self._hover_started)/0.050)
        return [v+((1.0 if i==self.hover_item else 0.0)-v)*p for i,v in enumerate(self._hover_from)]

    def _side_width_at(self, now=None):
        now = time.perf_counter() if now is None else now
        p = bezier_ease((now-self._side_started)/SIDEBAR_EXPAND_SECONDS,0.2,0.0,0.0,1.0)
        return self._side_from+(self._side_to-self._side_from)*p

    def _sel_fill(self):
        return mix(SIDE,TEXT,0.08)

    def _side_click(self, e):
        self.side.focus_set()
        if self.px(12) <= e.x <= self.px(56) and self.px(H-62) <= e.y <= self.px(H-18):
            self._toggle_side()
            return
        for i in range(len(PANE_KEYS)):
            x, y, _ = self._item_rect(i)
            if x <= e.x <= self.px(self.side_w.value)-self.px(12) and y <= e.y <= y+self.px(44):
                self._go(i)
                return

    def _side_motion(self, e):
        idx = -1
        if e is not None:
            for i in range(len(PANE_KEYS)):
                x, y, _r = self._item_rect(i)
                if x <= e.x <= x + (self.px(self.side_w.value) - self.px(24)) and \
                        y <= e.y <= y + self.px(44):
                    idx = i
                    break
        if idx != self.hover_item:
            now = time.perf_counter()
            self._hover_from = self._side_hover_values(now)
            self._hover_started = now
            self._sidebar_animation_dirty=True
            self.hover_item = idx
            self._draw_side()
        toggle = e is not None and self.px(12) <= e.x <= self.px(56) and self.px(H-62) <= e.y <= self.px(H-18)
        self.side.configure(cursor="hand2" if idx >= 0 or toggle else "")

    def _toggle_side(self):
        self._close_drop()
        now = time.perf_counter()
        self._side_from = self._side_width_at(now)
        self.collapsed = not self.collapsed
        self._side_to = float(SIDE_MINI if self.collapsed else SIDE_W)
        self._side_started = now
        self._sidebar_animation_dirty=True
        self.side_w.set(self._side_to)
        self._save_cfg()

    def _go(self, i):
        if i == self.page or not 0 <= i < len(PANE_KEYS):
            return
        now = time.perf_counter()
        self._nav_from = self._nav_marker_bounds(now)
        self._nav_fill_from = self._nav_fill_values(now)
        centre = 108+i*52+22
        self._nav_target = (centre-8.0,centre+8.0)
        self.nav_started = now
        if now-self._nav_pop_started[i]>=SIDEBAR_ICON_SECONDS:
            self._nav_pop_started[i]=now
        self._sidebar_animation_dirty=True
        self.page = i
        self._draw_side()
        # FlClash's desktop branch jumps to the content page; it does not slide it.
        self._render_page()

    def _render_page(self):
        self._close_drop()
        self.cv.delete("page")
        for w in self.pane_body.winfo_children():
            w.destroy()
        self.pane_body.place_forget()
        for attr in ("sl_cv", "sw_cv", "cfg_status", "cfg_auto_lbl", "ring_item", "ring_arc",
                     "btn_rect", "btn_text", "t_main", "t_sub", "t_detail", "fps_big", "sel_cv",
                     "primary_control", "stat_path", "fps_feedback"):
            setattr(self, attr, None)
        self._stat_items = []
        self._ring_key = None
        self._fx = []
        self.btn_hover_t = 0.0
        self.btn_hover = 0.0
        self._button_hover_from = 0.0
        self._button_hover_started = -1e9
        self.btn_pressed = False
        self._button_key = None
        self._status_render_key = None
        self.btn_scale.snap(1.0)
        self.cv.create_text(self.px(PAD), self.px(33), anchor="w", text=self.t(PANE_KEYS[self.page]),
                            fill=TEXT, font=self.f(23, "bold"), tags=("page",))
        self._label(PAD, 61, self.t(SUB_KEYS[self.page]), 12, SUB)
        if self.page == 0:
            self._draw_dash()
        else:
            self._draw_settings_card()

    def _card(self, x, y, w, h, r=16):
        return self._rr(self.cv, self.px(x), self.px(y), self.px(x+w), self.px(y+h), self.px(r),
                        fill=CARD, outline=LINE, width=max(1, self.px(1)), tags=("page",))

    def _label(self, x, y, text, size=11, color=None, anchor="w"):
        return self.cv.create_text(self.px(x), self.px(y), anchor=anchor,
                                   text=text, fill=color or MUTED,
                                   font=self.f(size), tags=("page",))

    def _draw_dash(self):
        c = self.cv
        self.btn_label = self.t({"idle": "start", "busy": "busy_btn", "ok": "stop", "fail": "retry"}[self.state])
        if HAS_PIL:
            self._wave_photo = ImageTk.PhotoImage(flower_status_card(524,286,self.S,
                dark=self._resolved=="dark",base=CARD,wave=mix(CARD,BLUE,0.10 if self._resolved=="dark" else 0.07),
                radius=24,outline=LINE))
            c.create_image(self.px(PAD),self.px(90),anchor="nw",image=self._wave_photo,tags=("page",))
        else:
            self._card(PAD,90,524,286,24)
        self._card(566, 90, 316, 286)
        self._card(PAD, 392, 274, 142)
        self._card(316, 392, 274, 142)
        self._card(606, 392, 276, 142)
        self._card(PAD, 550, 856, 124)
        self.status_dot = c.create_oval(self.px(50),self.px(118),self.px(56),self.px(124),
                                        fill=MUTED,outline="",tags=("page",))
        self._label(64,122,self.t("stat_state"),12,SUB)
        self.t_main = c.create_text(self.px(50),self.px(222),anchor="w",fill=TEXT,
                                    font=self.f(38,"bold"),width=self.px(300),tags=("page",))
        self.t_sub = self._label(50,266,"",12,SUB)
        self.t_detail = c.create_text(self.px(50),self.px(290),anchor="nw",fill=RED_TX,
                                      font=self.f(11),width=self.px(290),justify="left",tags=("page",))
        self.t_action_hint = self._label(50,350,self.t("hint_start"),11,SUB)
        self.btn_cx,self.btn_cy,self.btn_r = self.px(445),self.px(222),self.px(56)
        self.btn_w=self.btn_h=self.px(112)
        if HAS_PIL:
            self.btn_rect=c.create_image(self.btn_cx,self.btn_cy,tags=("page","primary"))
        else:
            self.btn_rect=c.create_polygon(0,0,0,0,0,0,fill=BLUE,outline="",tags=("page","primary"))
        self.btn_tri=c.create_polygon(0,0,0,0,0,0,fill="#ffffff",outline="",state="hidden",tags=("page",))
        self.btn_sq=c.create_line(0,0,0,0,fill="#ffffff",width=self.px(5),capstyle="round",state="hidden",tags=("page",))
        self.btn_pause2=c.create_line(0,0,0,0,fill="#ffffff",width=self.px(5),capstyle="round",state="hidden",tags=("page",))
        self.btn_label_bg=None
        self.btn_text=None
        self.fx_items,self.btn_dots=[],[]
        c.tag_bind("primary","<ButtonPress-1>",self._primary_press_event)
        c.bind("<ButtonRelease-1>",self._primary_release_event)
        c.bind("<Motion>",self._primary_motion)
        c.bind("<Leave>",lambda e:self._btn_enter(False))
        c.configure(takefocus=1)
        c.bind("<Return>",self._primary_key)
        c.bind("<space>",self._primary_key)
        c.bind("<FocusIn>",lambda e:self._btn_enter(True))
        c.bind("<FocusOut>",lambda e:self._btn_enter(False))
        self._label(590, 122, self.t("stat_target"), 12, SUB)
        self.stat_target = c.create_text(self.px(590), self.px(192), anchor="w", text=self.info["target"],
                                         fill=TEXT, font=self.f(38, "bold", mono=True), tags=("page",))
        self._label(590, 252, self.t("hint_fps"), 12)
        self._canvas_link(590, 316, self.t("nav_fps"), lambda: self._go(2))
        for x, key, attr, value in ((50, "stat_pid", "stat_pid", self.info["pid"]),
                                    (340, "stat_patch", "stat_patch", self.info["patch"])):
            self._label(x, 422, self.t(key), 12, SUB)
            item = c.create_text(self.px(x), self.px(470), anchor="w", text=value, fill=TEXT,
                                  font=self.f(23, "bold", mono=(key == "stat_pid")),
                                  width=self.px(230), tags=("page",))
            setattr(self, attr, item)
        self._label(630, 422, self.t("stat_lang"), 12, SUB)
        c.create_text(self.px(630), self.px(470), anchor="w", text=dict(LANGS).get(self.lang, ""),
                      fill=TEXT, font=self.f(16, "bold"), width=self.px(230), tags=("page",))
        self._canvas_link(630, 510, self.t("nav_lang"), lambda: self._go(4), 11)
        self._label(50, 580, self.t("stat_path"), 12, SUB)
        self._canvas_link(858, 580, self.t("nav_cfg"), lambda: self._go(3), 12, "e")
        self.stat_path = c.create_text(self.px(50), self.px(615), anchor="nw", fill=TEXT,
                                       font=self.f(12), width=self.px(796), tags=("page",))
        self._stat_items = [("target", self.stat_target), ("pid", self.stat_pid), ("patch", self.stat_patch)]
        self._refresh_stats()
        self._render_ring()
        self._render_button()

    def _primary_key(self, event):
        if self.page == 0 and self.btn_mode != "busy":
            self.btn_pressed=True
            self._btn_release()
        return "break"

    def _primary_hit(self,x,y):
        if self.page!=0 or getattr(self,"btn_rect",None) is None:
            return False
        radius=self.btn_r+self.px(5)
        return (x-self.btn_cx)**2+(y-self.btn_cy)**2<=radius**2

    def _primary_motion(self, event):
        if self.page==0:
            self._btn_enter(self._primary_hit(event.x,event.y))

    def _primary_press_event(self, event):
        if self._primary_hit(event.x,event.y):
            self._btn_press()

    def _primary_release_event(self, event):
        if self.page==0 and self._primary_hit(event.x,event.y):
            self._btn_release()
        else:
            self._btn_enter(False)

    def _canvas_link(self, x, y, text, callback, size=12, anchor="w"):
        tag = "link_" + str(len(self.cv.find_all()))
        self.cv.create_text(self.px(x), self.px(y), text=text + "  ›", anchor=anchor,
                            fill=BLUE_HI if self._resolved == "dark" else BLUE, font=self.f(size), tags=("page", tag))
        self.cv.tag_bind(tag, "<Button-1>", lambda e: callback())
        self.cv.tag_bind(tag, "<Enter>", lambda e: self.cv.configure(cursor="hand2"))
        self.cv.tag_bind(tag, "<Leave>", lambda e: self.cv.configure(cursor=""))

    def _draw_settings_card(self):
        self._card(PAD, 90, 856, 434)
        self._label(54, 124, self.t(PANE_KEYS[self.page]), 14, TEXT)
        self.cv.create_line(self.px(54), self.px(151), self.px(854), self.px(151), fill=LINE, tags=("page",))
        self.pane_body.place(x=self.px(54), y=self.px(176), width=self.px(800), height=self.px(320))
        self.pane_body.tkraise()
        self._render_pane()

    def _render_pane(self):
        renderers = (self._render_skin_pane, self._render_fps_pane, self._render_config_pane,
                     self._render_lang_pane, self._render_about_pane)
        renderers[self.page-1]()

    def _make_select(self, y, current_text, on_pick):
        body = self.pane_body
        w, h = self.px(320), self.px(40)
        self.sel_cv = tk.Canvas(body, bg=CARD, highlightthickness=0, bd=0, cursor="hand2")
        self.sel_cv.place(x=0, y=self.px(y), width=w, height=h)
        self.sel_cv.configure(takefocus=1)
        self.sel_cv.bind("<Button-1>", lambda e: self._toggle_drop())
        for key in ("<Return>", "<space>", "<Down>"):
            self.sel_cv.bind(key, lambda e: (self._toggle_drop(), "break")[1])
        rect = self.sel_cv.create_polygon(self._rr_pts(1, 1, w-1, h-1, self.px(11)),
                                   smooth=True, fill=SEL_BG,
                                   outline=mix(LINE, TEXT, 0.14))
        self.sel_cv.create_text(self.px(14), h / 2.0, anchor="w",
                                text=current_text, fill=TEXT, font=self.f(13))
        self.sel_cv.create_text(w - self.px(16), h / 2.0, anchor="e", text="\u2304",
                                fill=SUB, font=self.f(12))
        self.sel_cv.bind("<FocusIn>", lambda e: self.sel_cv.itemconfig(rect, outline=BLUE, width=self.px(2)))
        self.sel_cv.bind("<FocusOut>", lambda e: self.sel_cv.itemconfig(rect, outline=LINE, width=1))
        self._drop_y = y + 46
        self._pick_cb = on_pick
        return w

    def _fill_drop(self, options, current_key):
        self._drop_opts = list(options)
        self._drop_cur = current_key

    def _close_drop(self):
        if getattr(self, "drop_cv", None) is not None:
            try:
                self.drop_cv.destroy()
            except Exception:
                pass
            self.drop_cv = None
        self.drop_open = False

    def _toggle_drop(self):
        if self.drop_open:
            self._close_drop()
            return
        opts = getattr(self, "_drop_opts", [])
        if not opts:
            return
        self.root.update_idletasks()
        rh, w = self.px(38), self.px(320)
        h = rh*len(opts) + self.px(8)
        x = self.sel_cv.winfo_rootx() - self.content.winfo_rootx()
        y = self.sel_cv.winfo_rooty() - self.content.winfo_rooty() + self.sel_cv.winfo_height() + self.px(6)
        y = min(y, self.px(H)-h-self.px(16))
        cv = tk.Canvas(self.content, bg=BG, highlightthickness=0, bd=0, takefocus=1)
        cv.place(x=x, y=y, width=w, height=h)
        tk.Misc.lift(cv)
        cv.bind("<Button-1>", self._drop_click)
        cv.bind("<Motion>", self._drop_move)
        cv.bind("<Leave>", lambda e: self._drop_hover(-1))
        cv.bind("<Up>", lambda e: self._drop_key(-1))
        cv.bind("<Down>", lambda e: self._drop_key(1))
        cv.bind("<Return>", self._drop_accept)
        cv.bind("<space>", self._drop_accept)
        self.drop_cv, self.drop_open = cv, True
        idx = next((i for i, item in enumerate(opts) if item[0] == self._drop_cur), 0)
        self._drop_hover(idx)
        cv.focus_set()

    def _drop_key(self, delta):
        self._drop_hover((getattr(self, "_drop_idx", 0)+delta) % len(self._drop_opts))
        return "break"

    def _drop_accept(self, event):
        if 0 <= self._drop_idx < len(self._drop_opts):
            key = self._drop_opts[self._drop_idx][0]
            self._close_drop()
            self._pick_cb(key)
        return "break"

    def _drop_hover(self, idx):
        cv = self.drop_cv
        if cv is None:
            return
        cv.delete("all")
        w = self.px(320)
        rh = self.px(38)
        h = rh * len(self._drop_opts) + self.px(8)
        cv.create_polygon(self._rr_pts(1, 1, w-1, h-1, self.px(12)), smooth=True,
                          fill=DROP_BG, outline=mix(LINE, TEXT, 0.15))
        for i, (key, label) in enumerate(self._drop_opts):
            y = self.px(4) + i * rh
            if i == idx:
                cv.create_polygon(self._rr_pts(self.px(4), y + self.px(2),
                                               w - self.px(4), y + rh - self.px(2),
                                               self.px(9)), smooth=True,
                                  fill=DROP_HOVER, outline="")
            cv.create_text(self.px(16), y + rh / 2.0, anchor="w", text=label,
                           fill=TEXT if key == self._drop_cur else SUB,
                           font=self.f(13, "bold" if key == self._drop_cur else "normal"))
            if key == self._drop_cur:
                cv.create_text(w - self.px(20), y + rh / 2.0, anchor="e",
                               text="\u2713", fill=BLUE, font=self.f(12, "bold"))
        self._drop_idx = idx

    def _drop_move(self, e):
        rh = self.px(38)
        i = int((e.y - self.px(4)) // rh)
        if not (0 <= i < len(self._drop_opts)):
            i = -1
        if i != getattr(self, "_drop_idx", -2):
            self._drop_hover(i)

    def _drop_click(self, e):
        rh = self.px(38)
        i = int((e.y - self.px(4)) // rh)
        opts = getattr(self, "_drop_opts", [])
        if 0 <= i < len(opts):
            key = opts[i][0]
            self._close_drop()
            self._pick_cb(key)

    def _choose_theme(self, key):
        if key != self.theme_mode:
            self._set_theme(key)

    def _choose_lang(self, key):
        if key != self.lang:
            self._set_lang(key)

    # ---- pane _render_skin_pane
    def _render_skin_pane(self):
        tk.Label(self.pane_body, text=self.t("appearance"), bg=CARD, fg=SUB,
                 font=self.f(12)).place(x=0, y=0)
        self._make_select(28, self._theme_label(), self._choose_theme)
        self._fill_drop([("light", self.t("theme_light")), ("dark", self.t("theme_dark")),
                         ("auto", self.t("theme_auto"))], self.theme_mode)
        # Small previews make both palettes visible before choosing.
        for i, key in enumerate(("light", "dark")):
            pal = THEMES[key]
            cv = tk.Canvas(self.pane_body, bg=CARD, highlightthickness=0, cursor="hand2", takefocus=1)
            cv.place(x=self.px(i*190), y=self.px(100), width=self.px(174), height=self.px(140))
            self._rr(cv, self.px(1), self.px(1), self.px(173), self.px(103), self.px(12),
                     fill=pal["BG"], outline=BLUE if self.theme_mode == key else LINE,
                     width=self.px(2) if self.theme_mode == key else 1)
            self._rr(cv, self.px(12), self.px(13), self.px(42), self.px(91), self.px(6),
                     fill=pal["SIDE"], outline=pal["LINE"])
            for row in range(3):
                cv.create_line(self.px(20), self.px(28+row*17), self.px(34), self.px(28+row*17),
                                fill=pal["BLUE"] if row == 0 else pal["MUTED"], width=self.px(3))
            self._rr(cv, self.px(53), self.px(13), self.px(160), self.px(58), self.px(7),
                     fill=pal["CARD"], outline=pal["LINE"])
            cv.create_line(self.px(66), self.px(30), self.px(113), self.px(30), fill=pal["TEXT"], width=self.px(3))
            cv.create_line(self.px(66), self.px(43), self.px(94), self.px(43), fill=pal["BLUE"], width=self.px(4))
            for col in range(2):
                self._rr(cv, self.px(53+col*57), self.px(68), self.px(103+col*57), self.px(91),
                         self.px(5), fill=pal["CARD"], outline=pal["LINE"])
            cv.create_text(self.px(87), self.px(124), text=self.t("theme_"+key), fill=TEXT, font=self.f(12))
            cv.bind("<Button-1>", lambda e, k=key: self._choose_theme(k))
            cv.bind("<Return>", lambda e, k=key: self._choose_theme(k))
            cv.bind("<space>", lambda e, k=key: self._choose_theme(k))

    def _theme_label(self):
        return {"light": self.t("theme_light"), "dark": self.t("theme_dark"),
                "auto": self.t("theme_auto")}.get(self.theme_mode, "")

    # ---- pane _render_fps_pane
    def _render_fps_pane(self):
        body = self.pane_body
        tk.Label(body, text=self.t("fps_target"), bg=CARD, fg=SUB,
                 font=self.f(13), anchor="w").place(x=0, y=0)
        self.fps_big = tk.Label(body, text=self._fps_label(), bg=CARD, fg=TEXT,
                                font=self.f(30, "bold", mono=True), anchor="w")
        self.fps_big.place(x=0, y=self.px(26))

        w = self.px(520)
        self.sl_pad = self.px(52)
        self.sl_w = w
        self.sl_cv = tk.Canvas(body, bg=CARD, highlightthickness=0, bd=0, cursor="hand2")
        self.sl_cv.place(x=0, y=self.px(96), width=w, height=self.px(84))

        self.sl_idx = self._fps_index(self.target_fps)
        if getattr(self, "sl_x", None) is None:
            self.sl_x = Spring(self._sl_pos(self.sl_idx), 420.0, 30.0)
        else:
            self.sl_x.snap(self._sl_pos(self.sl_idx))

        cy = self.px(26)
        cv = self.sl_cv
        cv.create_polygon(self._rr_pts(self.sl_pad, cy - self.px(4),
                                       w - self.sl_pad, cy + self.px(4), self.px(4)),
                          smooth=True, fill=TRACK, outline="")
        self.sl_fill = cv.create_polygon(
            self._rr_pts(self.sl_pad, cy - self.px(4), self.sl_pad + 2,
                         cy + self.px(4), self.px(4)),
            smooth=True, fill=BLUE, outline="")
        self.sl_labels = []
        for i, (val, name) in enumerate(FPS_STOPS):
            x = self._sl_pos(i)
            txt = self.t("unlimited") if val >= 1000 else name
            active = val == self.target_fps
            it = cv.create_text(x, cy + self.px(30), text=txt,
                                fill=TEXT if active else MUTED,
                                font=self.f(12, "bold" if active else "normal"))
            self.sl_labels.append(it)

        self.sl_thumb_ring = cv.create_oval(0, 0, 0, 0, fill=CARD, outline="")
        self.sl_thumb = cv.create_oval(0, 0, 0, 0, fill="#ffffff", outline=LINE, width=1)
        cv.configure(takefocus=1)
        cv.bind("<Left>", lambda e: self._fps_step(-1))
        cv.bind("<Right>", lambda e: self._fps_step(1))
        cv.bind("<Button-1>", self._sl_down)
        cv.bind("<B1-Motion>", self._sl_move)
        cv.bind("<ButtonRelease-1>", self._sl_up)
        self._sl_paint()
        tk.Label(body, text=self.t("custom_fps"), bg=CARD, fg=SUB, font=self.f(12)).place(x=0, y=self.px(196))
        self.custom_fps_var = tk.StringVar(value=str(self.target_fps))
        self._rounded_entry(body, 0, 224, 132, 38, self.custom_fps_var,
                            size=13, mono=True, on_submit=self._commit_custom_fps)
        self._text_button(body, 144, 224, 116, self.t("apply_fps"), self._commit_custom_fps)
        self.fps_feedback = tk.Label(body, text=self.t("fps_hint"), bg=CARD, fg=MUTED,
                                     font=self.f(11), anchor="w")
        self.fps_feedback.place(x=0, y=self.px(278), width=self.px(780))

    def _fps_step(self, delta):
        self.sl_idx = max(0, min(len(FPS_STOPS)-1, self.sl_idx+delta))
        self._sl_labels()
        self.sl_x.set(self._sl_pos(self.sl_idx))
        return "break"

    def _commit_custom_fps(self):
        raw = self.custom_fps_var.get().strip()
        if not 2 <= len(raw) <= 4 or not raw.isascii() or not raw.isdigit() or not 60 <= int(raw) <= 1000:
            self.fps_feedback.configure(text=self.t("err_fps"), fg=RED_TX)
            return
        self.target_fps = int(raw)
        self.fps_var.set(raw)
        self.info["target"] = self._fps_label()
        self.sl_idx = self._fps_index(self.target_fps)
        self.sl_x.set(self._sl_pos(self.sl_idx))
        for i, item in enumerate(self.sl_labels):
            active = FPS_STOPS[i][0] == self.target_fps
            self.sl_cv.itemconfig(item, fill=BLUE if active else MUTED,
                                  font=self.f(12, "bold" if active else "normal"))
        self.fps_big.configure(text=self._fps_label())
        self.fps_feedback.configure(text=self.t("fps_hint"), fg=MUTED)
        self._save_cfg()

    # ---- pane _fps_index
    def _fps_index(self, fps):
        best, bi = 1e9, 1
        for i, (v, _n) in enumerate(FPS_STOPS):
            d = abs(v - fps)
            if d < best:
                best, bi = d, i
        return bi

    # ---- pane _sl_pos
    def _sl_pos(self, i):
        span = self.sl_w - 2 * self.sl_pad
        return self.sl_pad + span * i / float(len(FPS_STOPS) - 1)

    # ---- pane _sl_paint
    def _sl_paint(self):
        cv = getattr(self, "sl_cv", None)
        if cv is None:
            return
        cy = self.px(26)
        x = max(self.sl_pad, min(self.sl_w - self.sl_pad, self.sl_x.value))
        cv.coords(self.sl_fill, *self._rr_pts(self.sl_pad, cy - self.px(4),
                                              max(self.sl_pad + self.px(8), x),
                                              cy + self.px(4), self.px(4)))
        r = self.px(12)
        cv.coords(self.sl_thumb_ring, x - r - self.px(3), cy - r - self.px(3),
                  x + r + self.px(3), cy + r + self.px(3))
        cv.coords(self.sl_thumb, x - r, cy - r, x + r, cy + r)

    # ---- pane _sl_index_at
    def _sl_index_at(self, x):
        span = self.sl_w - 2 * self.sl_pad
        if span <= 0:
            return 0
        i = int(round((x - self.sl_pad) / span * (len(FPS_STOPS) - 1)))
        return max(0, min(len(FPS_STOPS) - 1, i))

    # ---- pane _sl_set
    def _sl_set(self, x):
        self.sl_x.set(max(self.sl_pad, min(self.sl_w - self.sl_pad, x)))
        i = self._sl_index_at(x)
        if i != self.sl_idx:
            self.sl_idx = i
            self._sl_labels()

    # ---- pane _sl_labels
    def _sl_labels(self):
        for i, it in enumerate(self.sl_labels):
            self.sl_cv.itemconfig(
                it, fill=TEXT if i == self.sl_idx else MUTED,
                font=self.f(12, "bold" if i == self.sl_idx else "normal"))
        self.target_fps = FPS_STOPS[self.sl_idx][0]
        self.fps_var.set(str(self.target_fps))
        self.info["target"] = self._fps_label()
        big = getattr(self, "fps_big", None)
        if big is not None:
            big.configure(text=self._fps_label())
        if getattr(self, "custom_fps_var", None) is not None:
            self.custom_fps_var.set(str(self.target_fps))
        if getattr(self, "fps_feedback", None) is not None:
            self.fps_feedback.configure(text=self.t("fps_hint"), fg=MUTED)
        self._save_cfg()
        self._refresh_stats()

    # ---- pane _sl_down
    def _sl_down(self, e):
        self.sl_drag = True
        self._sl_set(e.x)

    # ---- pane _sl_move
    def _sl_move(self, e):
        if getattr(self, "sl_drag", False):
            self._sl_set(e.x)

    # ---- pane _sl_up
    def _sl_up(self, e):
        self.sl_drag = False
        self.sl_idx = self._sl_index_at(e.x)
        self._sl_labels()
        self.sl_x.set(self._sl_pos(self.sl_idx))

    def _render_config_pane(self):
        body = self.pane_body
        tk.Label(body, text=self.t("game_exe"), bg=CARD, fg=SUB, font=self.f(12)).place(x=0, y=0)
        self._rounded_entry(body, 0, 28, 500, 40, self.path_var,
                            on_submit=self._save_cfg, on_blur=self._save_cfg)
        self._text_button(body, 512, 28, 136, self.t("browse"), self._browse_exe)
        self._text_button(body, 660, 28, 140, self.t("auto_search"), self._auto_find)
        self.cfg_status = tk.Label(body, text=self._path_status(), bg=CARD, fg=MUTED,
                                   font=self.f(11), anchor="nw", justify="left", wraplength=self.px(780))
        self.cfg_status.place(x=0, y=self.px(86), width=self.px(780), height=self.px(66))
        divider = tk.Frame(body, bg=LINE)
        divider.place(x=0, y=self.px(168), width=self.px(800), height=1)
        tk.Label(body, text=self.t("minimize_opt"), bg=CARD, fg=TEXT, font=self.f(13),
                 anchor="w").place(x=0, y=self.px(194), width=self.px(650))
        tk.Label(body, text=self.t("minimize_hint"), bg=CARD, fg=MUTED, font=self.f(11),
                 anchor="w").place(x=0, y=self.px(224), width=self.px(650))
        self.sw_cv = tk.Canvas(body, bg=CARD, highlightthickness=0, bd=0, cursor="hand2", takefocus=1)
        self.sw_cv.place(x=self.px(736), y=self.px(195), width=self.px(64), height=self.px(36))
        self.sw = Spring(1.0 if self.minimize else 0.0, 420.0, 26.0)
        self.sw_cv.bind("<Button-1>", lambda e: self._toggle_minimize())
        self.sw_cv.bind("<space>", lambda e: (self._toggle_minimize(), "break")[1])
        self.sw_cv.bind("<Return>", lambda e: (self._toggle_minimize(), "break")[1])
        self._draw_switch()

    def _rounded_entry(self, parent, x, y, width, height, variable,
                       size=12, mono=False, on_submit=None, on_blur=None):
        """Use one rounded shell for editable fields, including focus states."""
        field = tk.Canvas(parent, bg=CARD, highlightthickness=0, bd=0)
        w, h = self.px(width), self.px(height)
        field.place(x=self.px(x), y=self.px(y), width=w, height=h)
        border = self._rr(field, 1, 1, w-1, h-1, self.px(11),
                          fill=SEL_BG, outline=LINE, width=max(1, self.px(1)))
        entry = tk.Entry(field, textvariable=variable, bg=SEL_BG, fg=TEXT,
                         insertbackground=BLUE, relief="flat", bd=0,
                         highlightthickness=0, font=self.f(size, mono=mono))
        inset, top = self.px(13), self.px(7)
        entry.place(x=inset, y=top, width=w-2*inset, height=h-2*top)
        field.bind("<Button-1>", lambda e: entry.focus_set())
        entry.bind("<FocusIn>", lambda e: field.itemconfig(border, outline=BLUE))
        def leave_field(event):
            if field.winfo_exists():
                field.itemconfig(border, outline=LINE)
            if on_blur is not None:
                on_blur()
        entry.bind("<FocusOut>", leave_field)
        if on_submit is not None:
            entry.bind("<Return>", lambda e: on_submit())
        return entry

    def _text_button(self, parent, x, y, width, text, command):
        button = tk.Canvas(parent, bg=CARD, highlightthickness=0, bd=0, cursor="hand2", takefocus=1)
        w, h = self.px(width), self.px(40)
        button.place(x=self.px(x), y=self.px(y), width=w, height=h)
        rect = self._rr(button, 1, 1, w-1, h-1, self.px(9), fill=SEL_BG, outline=LINE)
        button.create_text(w/2, h/2, text=text, fill=TEXT, font=self.f(12), width=w-self.px(12))
        button.bind("<Enter>", lambda e: button.itemconfig(rect, fill=HOVER))
        button.bind("<Leave>", lambda e: button.itemconfig(rect, fill=SEL_BG))
        button.bind("<FocusIn>", lambda e: button.itemconfig(rect, outline=BLUE, width=self.px(2)))
        button.bind("<FocusOut>", lambda e: button.itemconfig(rect, outline=LINE, width=1))
        button.bind("<ButtonPress-1>", lambda e: button.focus_set())
        button.bind("<ButtonRelease-1>", lambda e: command() if 0 <= e.x <= w and 0 <= e.y <= h else None)
        def activate(event):
            command()
            return "break"
        button.bind("<Return>", activate)
        button.bind("<space>", activate)
        return button

    def _pill(self, cv, x1, y1, x2, y2, fill, tags=None):
        """真正的水滴胶囊：左右半圆 + 中段矩形。"""
        h = y2 - y1
        r = h / 2.0
        kw = {"fill": fill, "outline": ""}
        if tags:
            kw["tags"] = tags
        cv.create_oval(x1, y1, x1 + h, y2, **kw)
        cv.create_oval(x2 - h, y1, x2, y2, **kw)
        cv.create_rectangle(x1 + r, y1, x2 - r, y2, **kw)

    def _draw_switch(self):
        cv = getattr(self, "sw_cv", None)
        if cv is None:
            return
        cv.delete("all")
        w, h = self.px(54), self.px(30)
        k = max(0.0, min(1.0, self.sw.value))
        on_col = BLUE
        off_col = mix(CARD, TEXT, 0.30)
        track = mix(off_col, on_col, k)
        self._pill(cv, 0, 0, w, h, track)
        r = h / 2.0 - self.px(5)
        cx = self.px(5) + r + (w - 2 * (self.px(5) + r)) * k
        cv.create_oval(cx - r, h / 2.0 - r, cx + r, h / 2.0 + r,
                       fill="#ffffff", outline="")

    def _toggle_minimize(self):
        self.minimize = not self.minimize
        self.sw.set(1.0 if self.minimize else 0.0)
        self._save_cfg()

    def _path_status(self):
        p = self.path_var.get().strip()
        if p and os.path.isfile(p):
            return self.t("imported", p=os.path.basename(p))
        return self.t("not_imported")

    # ---- pane _browse_exe
    def _browse_exe(self):
        init = os.path.dirname(self.path_var.get()) if self.path_var.get() else "C:\\"
        p = filedialog.askopenfilename(
            title=self.t("dlg_title"), initialdir=init,
            filetypes=[(self.t("dlg_exe"), "*.exe"), (self.t("dlg_all"), "*.*")])
        if p:
            self.path_var.set(os.path.normpath(p))
            if self.cfg_status is not None:
                self.cfg_status.configure(text=self._path_status(), fg=GREEN_TX)

    # ---- pane _auto_find
    def _auto_find(self):
        st = self.cfg_status
        if st is not None:
            st.configure(text=self.t("searching"), fg=SUB)
        self.root.update_idletasks()
        paths = core.guess_game_paths()
        if paths:
            self.path_var.set(paths[0])
            if st is not None:
                st.configure(text=self.t("found_import", p=paths[0]), fg=GREEN_TX)
        elif st is not None:
            st.configure(text=self.t("not_found"), fg=RED_TX)

    # ---- pane _render_lang_pane
    def _render_lang_pane(self):
        body = self.pane_body
        tk.Label(body, text=self.t("language"), bg=CARD, fg=SUB,
                 font=self.f(12)).place(x=0, y=0)
        cur = dict(LANGS).get(self.lang, LANGS[0][1])
        self._make_select(26, cur, self._choose_lang)
        self._fill_drop(LANGS, self.lang)

    # ---- pane _render_about_pane
    def _render_about_pane(self):
        body = self.pane_body
        rows = ((self.t("version"), VERSION), (self.t("updated"), UPDATED))
        for i, (k, v) in enumerate(rows):
            y = self.px(8 + i * 56)
            tk.Label(body, text=k, bg=CARD, fg=MUTED, font=self.f(13),
                     anchor="w").place(x=0, y=y, width=self.px(96))
            tk.Label(body, text=v, bg=CARD, fg=TEXT, font=self.f(14),
                     anchor="w").place(x=self.px(100), y=y, width=self.px(300))
        tk.Label(body,text=('使用许可' if self.lang.startswith('zh') else 'License'),bg=CARD,fg=MUTED,font=self.f(13),
                 anchor='w').place(x=0,y=self.px(120),width=self.px(96))
        tk.Label(body,text=('仅限非商业用途 · 禁止商用' if self.lang.startswith('zh') else 'Non-commercial use only'),
                 bg=CARD,fg=TEXT,font=self.f(14),anchor='w').place(x=self.px(100),y=self.px(120))
        self._text_button(body,0,180,220,('GitHub 项目仓库' if self.lang.startswith('zh') else 'GitHub repository'),self._open_repository)
        link=tk.Label(body,text=REPOSITORY_URL,bg=CARD,fg=BLUE_HI,font=self.f(12),
                      anchor='w',cursor='hand2',takefocus=1)
        link.place(x=0,y=self.px(238),width=self.px(800))
        for event in ('<Button-1>','<Return>','<space>'):
            link.bind(event,lambda e:self._open_repository())

    def _open_repository(self):
        if os.name=='nt':
            os.startfile(REPOSITORY_URL)
        else:
            import webbrowser
            webbrowser.open_new_tab(REPOSITORY_URL)


    # ------------------------------------------------------------ 数据流
    def log(self, msg, color=None):
        self.history.append(str(msg))
        if len(self.history) > 400:
            del self.history[:200]

    def _post(self, state, detail="", **info):
        self.q.put(("state", (state, detail, info)))

    def _pump(self):
        try:
            while True:
                kind, payload = self.q.get_nowait()
                if kind == "state":
                    self._apply(*payload)
        except queue.Empty:
            pass
        self.root.after(60, self._pump)

    def _apply(self, st, detail="", info=None):
        info = info or {}
        now=time.perf_counter()
        previous_color=self._status_color(now)
        morph,glyph=self._button_motion_values(now)
        self._morph_from,self._glyph_from=morph,glyph
        self._morph_to=0.0 if st=="busy" else 1.0
        self._glyph_to=1.0 if st=="ok" else 0.0
        self._morph_started=now
        self._status_from=previous_color
        self._status_started=now
        self.btn_pressed=False
        self.state, self.detail = st, detail
        self.info.update(info)
        if st == "ok":
            self.active_fps = getattr(self.unlocker, "target_fps", None) or self.active_fps or self.target_fps
            self.btn_mode, self.btn_label = "stop", self.t("stop")
            self.progress.set(1.0)
        elif st == "busy":
            self.btn_mode, self.btn_label = "busy", self.t("busy_btn")
            self.progress.set(0.0)
            self.pulse = max(self.pulse, 1.0)
            self.btn_scale.set(1.0)
        elif st == "fail":
            self.info["patch"] = "\u2014"
            self.btn_mode, self.btn_label = "start", self.t("retry")
            self.progress.set(1.0)
        else:
            self.active_fps = None
            self.info["pid"] = "\u2014"
            self.info["patch"] = "\u2014"
            self.btn_mode, self.btn_label = "start", self.t("start")
            self.progress.set(0.0)
        if getattr(self, "btn_text", None) is not None:
            self.cv.itemconfig(self.btn_text, text=self.btn_label)
        self._refresh_stats()

    def _refresh_stats(self):
        if self.page != 0:
            return
        for key, item in getattr(self, "_stat_items", []):
            self.cv.itemconfig(item, text=self.info.get(key, "—"))
        if getattr(self, "stat_patch", None):
            self.cv.itemconfig(self.stat_patch, fill=GREEN_TX if self.state == "ok" else TEXT)
        if getattr(self, "stat_path", None):
            path = self.path_var.get().strip()
            # Keep the entire stored path; bound only its dashboard presentation.
            shown = path if len(path) <= 160 else path[:66] + " … " + path[-90:]
            self.cv.itemconfig(self.stat_path, text=shown or self.t("not_imported"),
                               fill=TEXT if path else MUTED)

    def _path_changed(self, *_):
        self._refresh_stats()
        if self.cfg_status is not None:
            self.cfg_status.configure(text=self._path_status(), fg=MUTED)
        self._save_cfg()

    def _tick(self):
        now=time.perf_counter()
        dt=min(0.05,max(0.001,now-self._t_last))
        self._t_last=now
        self.phase=(self.phase+dt*1.9)%(2*math.pi)
        hp=bezier_ease((now-self._button_hover_started)/0.150,0.2,0.0,0.0,1.0)
        self.btn_hover=self._button_hover_from+(self.btn_hover_t-self._button_hover_from)*hp
        self.btn_scale.update(dt)
        self.progress.update(dt)
        old_w=self.px(self.side_w.value)
        self.side_w.value=self._side_width_at(now)
        new_w=self.px(self.side_w.value)
        if new_w!=old_w:
            self.main.place_configure(x=new_w)
            self.content.place_configure(x=self.px((SIDE_W-self.side_w.value)/2))
        sidebar_active=(now-self.nav_started<SIDEBAR_ICON_SECONDS or now-self._hover_started<0.050
                        or now-self._side_started<SIDEBAR_EXPAND_SECONDS)
        if new_w!=old_w or sidebar_active or self._sidebar_animation_dirty:
            self._draw_side()
            # The first frame after the deadline must paint the exact endpoint.
            self._sidebar_animation_dirty=sidebar_active
        if self.sl_cv is not None:
            self.sl_x.update(dt)
            self._sl_paint()
        if getattr(self,"sw_cv",None) is not None:
            self.sw.update(dt)
            self._draw_switch()
        if self.page==0 and getattr(self,"t_main",None) is not None:
            self._render_ring()
            self._render_button()
        # Account for the work done this frame rather than adding it to 16ms.
        # This keeps the animation clock close to 60Hz during interaction.
        spent=time.perf_counter()-now
        self.root.after(max(1,int(round(1000*(1/60-spent)))),self._tick)

    def _button_motion_values(self, now=None):
        now=time.perf_counter() if now is None else now
        t=motion_clamp((now-self._morph_started)/BUTTON_MORPH_SECONDS)
        curve=(0.175,0.885,0.32,1.275) if self._morph_to>=self._morph_from else (0.55,0.055,0.675,0.19)
        p=bezier_ease(t,*curve)
        return (self._morph_from+(self._morph_to-self._morph_from)*p,
                self._glyph_from+(self._glyph_to-self._glyph_from)*p)

    def _status_color(self, now=None):
        now=time.perf_counter() if now is None else now
        target={"idle":TEXT,"busy":BLUE_HI,"ok":GREEN_TX,"fail":RED_TX}[self.state]
        if self._status_from is None:
            return target
        p=bezier_ease((now-self._status_started)/0.220,0.2,0.0,0.0,1.0)
        return mix(self._status_from,target,p)

    def _ring_state(self):
        if self.state=="busy":
            return dict(main=self.t("s_busy"),sub=self.t("s_busy_sub"),fg=BLUE_HI)
        if self.state=="ok":
            return dict(main=self.t("s_ok"),sub=self.t("s_ok_sub",fps=self._fps_label(self.active_fps or self.target_fps)),fg=GREEN_TX)
        if self.state=="fail":
            return dict(main=self.t("s_fail"),sub=self.t("s_fail_sub"),fg=RED_TX)
        return dict(main=self.t("s_idle"),sub=self.t("s_idle_sub"),fg=TEXT)

    def _render_ripples(self):
        c = self.cv
        items = getattr(self, "fx_items", None)
        if not items:
            return
        live = []
        for f in self._fx:
            if f["t"] < 0:
                continue
            age = min(1.0, f["t"] / f.get("life", 0.85))
            ease = 1.0 - (1.0 - age) ** 3
            live.append((f["r"] + ease * f["grow"],
                         mix(f["base"], CARD, 0.15 + 0.75 * age)))
        for i, it in enumerate(items):
            if i < len(live):
                rad, col = live[i]
                c.coords(it, self.btn_cx - rad, self.btn_cy - rad,
                         self.btn_cx + rad, self.btn_cy + rad)
                c.itemconfig(it, state="normal", outline=col)
            else:
                c.itemconfig(it, state="hidden")

    def _render_ring(self):
        if self.page!=0 or getattr(self,"t_main",None) is None:
            return
        state=self._ring_state()
        color=self._status_color()
        key=(state["main"],state["sub"],color,self.detail,self.state,self.lang)
        if key==self._status_render_key:
            return
        self._status_render_key=key
        title_size = 38
        while title_size > 24 and self.root.tk.call(
                "font", "measure", self.f(title_size, "bold"), state["main"]) > self.px(300):
            title_size -= 1
        self.cv.itemconfig(self.t_main,text=state["main"],fill=color,
                           font=self.f(title_size,"bold"))
        self.cv.itemconfig(self.t_sub,text=state["sub"],fill=MUTED)
        self.cv.itemconfig(self.status_dot,fill=MUTED if self.state=="idle" else color)
        detail=self.detail[:140]+("…" if len(self.detail)>140 else "")
        self.cv.itemconfig(self.t_detail,text=detail,fill=RED_TX if self.state=="fail" else SUB)
        hint=self.t("hint_patch") if self.state=="ok" else self.t("s_busy_sub") if self.state=="busy" else self.t("hint_start")
        self.cv.itemconfig(self.t_action_hint,text="" if detail else hint)

    def _render_ring_image(self, s, ripples):
        r = s["r"]
        pad = self.px(14)
        outer = r
        for rr, _ in ripples:
            outer = max(outer, rr)
        D = int(2 * (outer + pad + 2))
        SS = 3
        S = D * SS
        img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        cx = cy = S / 2.0
        wpx = max(1, int(round(s["w"] * SS)))

        def _box(rad):
            return (cx - rad * SS, cy - rad * SS, cx + rad * SS, cy + rad * SS)

        for rr, col in ripples:
            d.ellipse(_box(rr), outline=hex2rgb(col) + (255,), width=max(1, SS))
        d.ellipse(_box(r), outline=hex2rgb(s["track"]) + (255,), width=wpx)

        if s["dots"]:
            n = 9
            head = (s["start"] / 360.0) * n
            for i in range(n):
                ang = -s["start"] - i * (360.0 / n)
                a = math.radians(ang)
                back = (head - i) % n / float(n)
                col = mix(s["fg"], s["track"], 0.15 + back * 0.85)
                rad = max(1.0, s["w"] * 0.62 * (1.0 - 0.45 * back))
                ex = cx + r * SS * math.cos(a)
                ey = cy + r * SS * math.sin(a)
                d.ellipse((ex - rad * SS, ey - rad * SS,
                           ex + rad * SS, ey + rad * SS), fill=hex2rgb(col) + (255,))

        if s["color"]:
            col = hex2rgb(s["color"]) + (255,)
            span = abs(s["extent"])
            p_start = -s["start"]
            d.arc(_box(r), start=p_start, end=p_start + span, fill=col, width=wpx)
            rad = s["w"] / 2.0
            for ang in (() if span > 350 else (p_start, p_start + span)):
                a = math.radians(ang)
                ex = cx + r * SS * math.cos(a)
                ey = cy + r * SS * math.sin(a)
                cr = rad * SS
                d.ellipse((ex - cr, ey - cr, ex + cr, ey + cr), fill=col)

        img = img.resize((D, D), Image.BOX)
        return ImageTk.PhotoImage(img)

    def _render_button(self):
        if self.page!=0 or getattr(self,"btn_rect",None) is None:
            return
        c=self.cv
        morph,glyph=self._button_motion_values()
        press=motion_clamp((1-self.btn_scale.value)/0.045)
        hover=motion_clamp(self.btn_hover)
        mode="busy" if self.btn_mode=="busy" else "retry" if self.state=="fail" else "pause" if self.btn_mode=="stop" else "play"
        phase=round(self.phase*12)/12 if mode=="busy" else 0.0
        image_key=(round(hover*24)/24,round(press*24)/24,round(morph*64)/64,round(glyph*64)/64,
                   phase,mode,self._resolved,self.S)
        key=(image_key,self.btn_label,self.cv.focus_get()==self.cv)
        if key==self._button_key:
            return
        self._button_key=key
        if HAS_PIL:
            photo=self._button_frames.get(image_key)
            if photo is None:
                photo=ImageTk.PhotoImage(flower_button(112,self.S,hover=image_key[0],press=image_key[1],
                    phase=phase,mode=mode,dark=self._resolved=="dark",accent="#3d86ff",
                    morph=image_key[2],glyph_progress=image_key[3]))
                self._button_frames[image_key]=photo
                if len(self._button_frames)>48:
                    self._button_frames.pop(next(iter(self._button_frames)))
            self._button_photo=photo
            c.itemconfig(self.btn_rect,image=photo)
        else:
            radius=self.btn_r*(1+0.024*hover-0.045*press)
            points=[]
            for x,y in MOTION_COOKIE9_POINTS:
                points.extend((self.btn_cx+(x-0.5)*radius*2,self.btn_cy+(y-0.5)*radius*2))
            c.coords(self.btn_rect,*points)
            c.itemconfig(self.btn_rect,fill=mix("#3d86ff","#ffffff",hover*0.08))
            x,y=self.btn_cx,self.btn_cy
            c.coords(self.btn_tri,x-self.px(6),y-self.px(10),x-self.px(6),y+self.px(10),x+self.px(10),y)
            c.itemconfig(self.btn_tri,state="hidden" if self.btn_mode=="stop" else "normal")
            for item,dx in ((self.btn_sq,-5),(self.btn_pause2,5)):
                c.coords(item,x+self.px(dx),y-self.px(8),x+self.px(dx),y+self.px(8))
                c.itemconfig(item,state="normal" if self.btn_mode=="stop" else "hidden")

    def _render_fx(self, dt):
        alive = []
        for fx in self._fx:
            fx["t"] += dt
            if fx["t"] > fx.get("life", 0.85):
                continue
            alive.append(fx)
        self._fx = alive

    def _btn_enter(self, on):
        target=1.0 if on else 0.0
        changed=target!=self.btn_hover_t
        if changed:
            self._button_hover_from=self.btn_hover
            self._button_hover_started=time.perf_counter()
            self.btn_hover_t=target
        if not on:
            self.btn_pressed=False
            self.btn_scale.set(1.0)
        if changed or on:
            self.cv.configure(cursor="hand2" if on and self.btn_mode!="busy" else "")

    def _btn_press(self):
        if self.page!=0 or self.btn_mode=="busy":
            return
        self.cv.focus_set()
        self.btn_pressed=True
        self._btn_enter(True)
        self.btn_scale.set(0.955)

    def _btn_release(self):
        pressed=self.btn_pressed
        self.btn_pressed=False
        self.btn_scale.set(1.0)
        if not pressed or self.page!=0 or self.btn_mode=="busy":
            return
        if self.btn_mode=="stop":
            self.on_stop()
        else:
            self.on_start()

    def _ring_ripple(self, strong=False):
        if not hasattr(self, "r0"):
            return
        if strong:
            scales = (1.00, 1.10)
            grow = self.px(14)
            base, gap = BLUE, 0.075
        else:
            scales = (1.02, 1.16)
            grow = self.px(10)
            base, gap = BLUE, 0.07
        for i, scale in enumerate(scales):
            self._fx.append({"t": -i * gap, "r": self.r0 * scale,
                             "grow": grow, "base": base, "life": 0.85})

    # ------------------------------------------------------------ 业务
    def _autodetect(self):
        if self.path_var.get().strip():
            return os.path.isfile(self.path_var.get().strip())
        paths = core.guess_game_paths()
        if paths:
            self.path_var.set(paths[0])
            return True
        return False

    def _read_fps(self):
        raw = self.fps_var.get().strip()
        if not raw.isdigit():
            return None
        v = max(60, min(1000, int(raw)))
        self.fps_var.set(str(v))
        self.target_fps = v
        self.info["target"] = self._fps_label()
        self._refresh_stats()
        return v

    def on_start(self):
        exe = self.path_var.get().strip().strip('"')
        if not exe or not os.path.isfile(exe):
            self._apply("fail", self.t("err_no_exe"))
            return
        fps = self._read_fps()
        if fps is None:
            self._apply("fail", self.t("err_fps"))
            return
        if self.unlocker:
            self.unlocker.release()
            self.unlocker = None
        self._apply("busy", "", {"target": self._fps_label(fps)})
        threading.Thread(target=self._worker_start, args=(exe, fps), daemon=True).start()
        if self.minimize:
            self.root.after(900, self._minimize_self)

    def _minimize_self(self):
        try:
            if self.state == "busy":
                self.root.iconify()
        except Exception:
            pass

    def _worker_start(self, exe, fps):
        try:
            running = core.find_game_pids()
            if running:
                self._do_attach(running[0][0], fps)
                return
            proc = core.launch_game(exe)
            pid = core.wait_game_pid(timeout=240, prefer_pid=proc.pid, log=self.log)
            if not pid:
                raise RuntimeError("no game process")
            self._do_attach(pid, fps)
        except Exception as e:
            msg = str(e)
            if "740" in msg or "\u63d0\u5347" in msg:
                msg = self.t("err_admin")
            elif "\u62d2\u7edd\u8bbf\u95ee" in msg or "error 5" in msg.lower():
                msg = self.t("err_access")
            self._post("fail", msg)

    def _do_attach(self, pid, fps):
        self._post("busy", "", pid="%d" % pid)
        self.unlocker = core.FpsUnlocker(log=self.log)
        self.unlocker.attach(pid, wait_module=90)
        self.unlocker.apply(fps)
        hardened = self.unlocker.install_patch(fps)
        time.sleep(0.6)
        self.unlocker.read_current()
        self.unlocker.start_keepalive(2.0)
        self._post("ok", "", pid="%d" % pid,
                   patch=self.t("patch_on") if hardened else self.t("patch_off"))

    def on_stop(self):
        if self.unlocker:
            self.unlocker.release()
            self.unlocker = None
        self._apply("idle", "")

    def _watch(self):
        if self.theme_mode == "auto":
            resolved = self._resolve_theme()
            if resolved != self._resolved:
                self._set_theme("auto")
        if self.state in ("ok", "busy") and self.unlocker and self.unlocker.pid:
            if not core.is_alive(self.unlocker.pid):
                self.unlocker.release()
                self.unlocker = None
                self._apply("idle", "")
        self.root.after(1500, self._watch)

    def on_close(self):
        self._save_cfg()
        try:
            if self.unlocker:
                self.unlocker.release()
        finally:
            self.root.destroy()


def run_auto(args):
    """--auto [帧率]：无界面自动启动并解锁，日志写到 %TEMP%\\genshin_fps_unlock.log"""
    import tempfile

    log_path = os.path.join(tempfile.gettempdir(), "genshin_fps_unlock.log")
    open(log_path, "w", encoding="utf-8").close()

    def log(msg, color=None):
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(time.strftime("%H:%M:%S ") + str(msg) + "\n")

    fps = 240
    for a in args:
        if a.isdigit():
            fps = max(60, min(1000, int(a)))

    log("自动模式启动，目标 %d FPS，日志 %s" % (fps, log_path))
    if not core.is_admin():
        log("失败：需要管理员权限运行")
        return 1
    if core.find_game_pids():
        log("失败：游戏已在运行。请先退出游戏，本工具必须在游戏启动瞬间接管进程")
        return 1
    paths = core.guess_game_paths()
    if not paths:
        log("失败：没找到游戏路径，请用图形界面手动选择一次")
        return 1

    exe = paths[0]
    log("游戏路径：%s" % exe)
    proc = core.launch_game(exe)
    log("已启动 PID=%d" % proc.pid)
    u = core.FpsUnlocker(log=log)
    try:
        addr = u.attach(proc.pid, wait_module=60)
        log("定位成功 0x%X，当前值 %s" % (addr, u.read_current()))
        u.apply(fps)
        hard = u.install_patch(fps)
        log("已写入 %d FPS，setter 加固=%s" % (fps, hard))
        u.start_keepalive(2.0)
    except Exception as e:
        log("失败：%s" % e)
        return 1

    while core.is_alive(proc.pid):
        time.sleep(2)
    log("游戏已退出")
    u.release()
    return 0


def main():
    if "--auto" in sys.argv:
        idx = sys.argv.index("--auto")
        return run_auto(sys.argv[idx + 1:])
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass
    root = tk.Tk()
    App(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    main()