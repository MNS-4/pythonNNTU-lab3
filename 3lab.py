# Лабораторная работа №3. Стеганография. Вариант 33.
# Метод кодирования по варианту: b3-B, b2-B, b1-B, b0-B
# (3, 2, 1, 0 биты байта, отвечающего за синий цвет).

from PIL import Image, ImageDraw, UnidentifiedImageError
from random import randint


def safe_input(prompt):
	# Безопасный ввод: перехватывает Ctrl+C и Ctrl+D, не давая программе упасть
	try:
		return input(prompt)
	except (EOFError, KeyboardInterrupt):
		print()
		return ""


def safe_open_image(filename):
	# Безопасное открытие изображения.
	# Возвращает объект Image или None, если что-то пошло не так.
	if filename == "":
		print("Ошибка: имя файла не указано.")
		return None
	try:
		img = Image.open(filename)
		# на всякий случай приводим к RGB (вдруг пришёл RGBA или палитра)
		if img.mode != "RGB":
			img = img.convert("RGB")
		return img
	except FileNotFoundError:
		print("Ошибка: файл", filename, "не найден.")
	except UnidentifiedImageError:
		print("Ошибка: файл", filename, "не является изображением.")
	except PermissionError:
		print("Ошибка: нет прав на чтение файла", filename)
	except Exception as e:
		print("Ошибка при открытии изображения:", e)
	return None


def read_keys(filename):
	# Читаем координаты из файла ключей (строки вида "(x, y)")
	coords = []
	if filename == "":
		print("Ошибка: имя файла ключей не указано.")
		return coords
	try:
		f = open(filename, 'r', encoding='utf-8')
	except FileNotFoundError:
		print("Ошибка: файл ключей", filename, "не найден.")
		return coords
	except PermissionError:
		print("Ошибка: нет прав на чтение файла ключей", filename)
		return coords
	except Exception as e:
		print("Ошибка при открытии файла ключей:", e)
		return coords

	for line in f:
		line = line.strip().strip('()')
		if line == "":
			continue
		parts = line.split(',')
		if len(parts) < 2:
			continue
		try:
			x = int(parts[0].strip())
			y = int(parts[1].strip())
			coords.append((x, y))
		except ValueError:
			# строка не содержит валидных координат — просто пропускаем
			continue
	f.close()
	return coords


def stega_decoding_full_byte():
	# Пункт 1: декодирование готового изображения
	img = safe_open_image(safe_input("Имя файла для декодирования: "))
	if img is None:
		return ""

	pix = img.load()
	width, height = img.size

	keys = read_keys(safe_input("Имя файла с ключем: "))
	if not keys:
		print("Ошибка: список ключей пуст.")
		return ""

	byte_list = []
	for key in keys:
		x, y = key
		# проверяем, что координата внутри изображения
		if x < 0 or x >= width or y < 0 or y >= height:
			print("Предупреждение: координата", key, "вне изображения, пропущена.")
			continue
		r, g, b = pix[key][0:3]   # берем синий байт пикселя целиком
		byte_list.append(b)

	if not byte_list:
		print("Ошибка: не удалось прочитать ни одного пикселя.")
		return ""

	# декодируем итоговую байтовую строку
	try:
		message = bytes(byte_list).decode('utf-8', errors='ignore')
	except Exception:
		message = bytes(byte_list).decode('cp1251', errors='ignore')
	return message


def stega_coding():
	# Пункт 2: кодирование сообщения в картинку
	# В младшие 4 бита канала B записывается ниббл сообщения.
	# Два пикселя = один символ (старший и младший ниббл).
	img = safe_open_image(safe_input("Имя файла для кодирования: "))
	if img is None:
		return

	draw = ImageDraw.Draw(img)             # создаем объект рисования
	width = img.size[0]                    # определяем ширину изображения
	height = img.size[1]                   # определяем высоту изображения
	pix = img.load()                       # выгружаем все пиксели изображения

	message = safe_input("Введите сообщение: ")  # ввод секретного текста
	if message == "":
		print("Ошибка: пустое сообщение.")
		return

	# переводим сообщение в байты. Пробуем cp1251, если не получится — utf-8
	try:
		message_bytes = message.encode('cp1251')
	except UnicodeEncodeError:
		print("Предупреждение: сообщение содержит символы вне cp1251,"
		      " используется utf-8.")
		message_bytes = message.encode('utf-8')

	# проверка, что картинка достаточно большая для сообщения
	need_pixels = len(message_bytes) * 2   # 2 пикселя на символ
	total_pixels = width * height
	if need_pixels > total_pixels:
		print("Ошибка: картинка слишком мала для такого сообщения.")
		print("Нужно пикселей:", need_pixels, " доступно:", total_pixels)
		return

	# открываем текстовый файл для ключей
	try:
		f = open('keys33_my.txt', 'w', encoding='utf-8')
	except PermissionError:
		print("Ошибка: нет прав на запись файла keys33_my.txt")
		return
	except Exception as e:
		print("Ошибка при открытии файла ключей на запись:", e)
		return

	first = True  # флаг для вывода информации по первому символу

	for elem in message_bytes:                         # для каждого байта сообщения:
		hi = (elem >> 4) & 0x0F                        # старший ниббл (биты 7..4)
		lo = elem & 0x0F                               # младший ниббл (биты 3..0)

		# первый пиксель пары хранит старший ниббл
		key1 = (randint(1, width - 1), randint(1, height - 1))
		r1, g1, b1 = pix[key1][0:3]                    # сохраняем R, G, B
		new_b1 = (b1 & 0xF0) | hi                      # меняем младшие 4 бита B на hi
		draw.point(key1, (r1, g1, new_b1))             # записываем новый пиксель
		f.write(str(key1) + '\n')                      # записываем (x,y) в keys33_my.txt

		# второй пиксель пары хранит младший ниббл
		key2 = (randint(1, width - 1), randint(1, height - 1))
		r2, g2, b2 = pix[key2][0:3]
		new_b2 = (b2 & 0xF0) | lo
		draw.point(key2, (r2, g2, new_b2))
		f.write(str(key2) + '\n')

		# вывод доказательства корректности для первого символа
		if first:
			print()
			print("--- Доказательство кодирования первого символа ---")
			print("Символ:", chr(elem), " код:", elem,
			      " биты:", format(elem, '08b'))
			print("Старший ниббл (b7 b6 b5 b4):", format(hi, '04b'))
			print("Младший ниббл (b3 b2 b1 b0):", format(lo, '04b'))
			print("Пиксель 1", key1, ": исходный B =", b1,
			      "(", format(b1, '08b'), ")",
			      " новый B =", new_b1, "(", format(new_b1, '08b'), ")")
			print("Пиксель 2", key2, ": исходный B =", b2,
			      "(", format(b2, '08b'), ")",
			      " новый B =", new_b2, "(", format(new_b2, '08b'), ")")
			print()
			first = False

	f.close()
	print('Ключ сохранен в файле keys33_my.txt')

	# безопасное сохранение изображения
	try:
		img.save("new33_my.png", "PNG")
		print('Измененное изображение в файле new33_my.png')
	except PermissionError:
		print("Ошибка: нет прав на запись файла new33_my.png")
	except Exception as e:
		print("Ошибка при сохранении изображения:", e)


def stega_decoding_my():
	# Пункт 3: декодирование того, что я сам закодировал
	# Берем младшие 4 бита B двух соседних ключей, склеиваем в байт.
	img = safe_open_image(safe_input("Имя файла для декодирования: "))
	if img is None:
		return ""

	pix = img.load()
	width, height = img.size

	keys = read_keys(safe_input("Имя файла с ключем: "))
	if not keys:
		print("Ошибка: список ключей пуст.")
		return ""

	# из каждого пикселя берем младшие 4 бита B
	nibbles = []
	for key in keys:
		x, y = key
		# проверяем, что координата внутри изображения
		if x < 0 or x >= width or y < 0 or y >= height:
			print("Предупреждение: координата", key, "вне изображения, пропущена.")
			continue
		b = pix[key][2]           # синий байт пикселя
		nibbles.append(b & 0x0F)  # младшие 4 бита

	if len(nibbles) < 2:
		print("Ошибка: недостаточно валидных пикселей для декодирования.")
		return ""

	# предупреждение о нечётном числе нибблов
	if len(nibbles) % 2 != 0:
		print("Предупреждение: число ключей нечётное, последний ниббл отброшен.")

	# собираем байты из пар: первый — старший, второй — младший
	raw = bytearray()
	for i in range(0, len(nibbles) - 1, 2):
		hi = nibbles[i]
		lo = nibbles[i + 1]
		raw.append((hi << 4) | lo)

	try:
		message = raw.decode('cp1251')
	except UnicodeDecodeError:
		message = raw.decode('utf-8', errors='ignore')
	return message


PROMPT = """
Выберите режим стеганографии:
1. Декодировать текст из готового изображения
2. Закодировать свой текст в изображение
3. Декодировать свой текст из изображения
q. Выход
"""


def main():
	# цикл, чтобы после каждой операции возвращаться в меню,
	# а не перезапускать программу вручную
	while True:
		print(PROMPT)
		user_inp = ""
		while user_inp not in ("1", "2", "3", "q"):
			user_inp = safe_input("Ваш выбор: ")
			if user_inp == "":
				# пустой ввод (Ctrl+D/Ctrl+C) — выходим
				print("Выход.")
				return

		if user_inp == "1":
			print("Декодирование готового изображения")
			print("Ваше сообщение: ", stega_decoding_full_byte())
		elif user_inp == "2":
			print("Кодирование")
			stega_coding()
		elif user_inp == "3":
			print("Декодирование своего изображения")
			print("Ваше сообщение: ", stega_decoding_my())
		elif user_inp == "q":
			print("Выход.")
			return


if __name__ == "__main__":
	# верхний уровень защиты: если что-то совсем непредвиденное
	# вылетело из main(), ловим и не падаем с трейсбеком.
	try:
		main()
	except KeyboardInterrupt:
		print("\nРабота прервана пользователем.")
	except Exception as e:
		print("Непредвиденная ошибка:", e)