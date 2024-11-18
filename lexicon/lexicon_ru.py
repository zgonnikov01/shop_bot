class Lexicon:
    class Admin:

        add_products__set_product_name = 'Введите название товара'
        add_products__set_description = 'Введите описание товара'
        add_products__set_stock = 'Введите количество единиц товара, готовых к отправке'
        add_products__set_picture = 'Отправьте картинку товара'
        add_products__success = 'Товар создан!'


        basic__start = 'Привет! Я - бот, который поможет тебе автоматизировать торговлю добавками. Внизу есть кнопочка MENU, нажми на неё, и ты увидишь, что я умею!'

        
        edit_products__select_product = 'Для редактирования товаров выберите нужный из списка'
        edit_products__select_field = 'Выберите то, что хотите отредактировать'
        edit_products__edit_field__text = ''
        edit_products__edit_field__picture = ''
        edit_products__save = '' # ???

        update_catalog__success = 'Данные успешно подгружены'
        update_catalog__set_pictures = 'Добавьте картинку товара'
        update_catalog__error = 'Произошёл сбой'

        add_track_number__request_number = 'Введите трек номер для заказа. Если нажали по ошибке, напишите /cancel'


        menu = {
            # '/edit_products': 'Изменить информацию о товаре',
            '/update_catalog': 'Подгрузить актуальный каталог из гугл-таблицы',
            '/spreadsheet': 'Получить ссылку на гугл-таблицу с данными о товарах и заказах'
            # '/add_product': 'Добавить новый товар'
        }

        bot_description = 'Бот-магазин YETIBIO\n\nАктуальный список товаров:\n'
    
    class User:
        basic__start = 'Привет!\n\nЯ - бот, который поможет тебе заказать нужные добавки быстро и удобно😌'

        sign_up__get_full_name = 'Давайте знакомиться!\n\nПришлите, пожалуйста, свои данные, которые необходимы для доставки заказа☝🏻\n\nНачнем, напишите свое ФИО\n\n❗️ Пример: Иванов Иван Иванович'
        sign_up__get_number = 'Пришлите, пожалуйста, свой номер телефона\n\n❗️ Пример: +7 XXX XXX XX XX'
        sign_up__get_address = 'Осталось немного🤏\n\nНапишите, пожалуйста, свой полный адрес!\nОчень важно придерживаться формата, указанного в примере👇🏻\n\n❗️ Пример: Воронежская обл, Алексеевский р-н, пос. Лесное, ул. Ореховая, д. 25'
        sign_up__get_postal_code = 'И наконец, укажите свой почтовый индекс!\n\n❗️ Пример: 355000'
        sign_up__fail = 'Что-то пошло не так. Мы уже работаем над вашей проблемой'
        sign_up__success = 'Готово👌🏻\n\nЕсли Вы допустили ошибку при вводе или данные изменились, их можно обновить☝🏻\n\nДля этого еще раз используйте команду\n/sign_up'

        sign_up__incorrect_number = 'Пожалуйста, введите свой настоящий номер телефона, он будет нужен для оплаты'
                
        show_help__ = 'Help'

        show_faq__ = 'FAQ'

        process_order__ = 'Для оформления заказа сначала нужно зарегистрироваться (команда /sign_up)'
        process_order__check_stock = 'Ввиду отсутствия в наличии из корзины были удалены некоторые позиции:\n\n'

        process_catalog_navigation__not_enough_product = 'К сожалению, в наличии нет столько единиц выбранного товара'

        msg__cart_is_empty = 'Корзина пуста'

        menu = {
            '/catalog': 'Открыть каталог',
            '/sign_up': 'Зарегистрироваться',
            '/cart': 'Посмотреть товары в корзине',
            '/help': 'Помощь',
            '/faq': 'Часто задаваемые вопросы'
        }

