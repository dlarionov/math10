# Репозитории и публичный сайт

[Открыть уроки](https://dlarionov.github.io/math10/).

GitFlic и GitHub содержат одну историю main. GitHub Pages публикует корень main по HTTPS. Файл `.nojekyll` позволяет отдавать готовые HTML без обработки Jekyll. Локальное открытие через index.html сохраняется.

## Настройка нового клона

Клонируйте основной репозиторий и настройте второй remote и два адреса отправки. Эти настройки локальны и не переносятся вместе с файлами Git:

```powershell
git clone https://gitflic.ru/project/dlarionov/math10.git
cd math10
git remote add github https://github.com/dlarionov/math10.git
git config --local --add remote.origin.pushurl https://gitflic.ru/project/dlarionov/math10.git
git config --local --add remote.origin.pushurl https://github.com/dlarionov/math10.git
git config --local user.name "math10 contributors"
git config --local user.email "contributors@math10.invalid"
```

Для существующего клона сначала проверьте `git remote -v`: повторно добавлять push URL не нужно. Не сохраняйте пароли или токены в URL и файлах проекта.

## Обычная работа

```powershell
git fetch origin
git fetch github
git log --oneline --left-right main...origin/main
git log --oneline --left-right main...github/main
```

Изучите новые удалённые коммиты до редактирования. Не исправляйте расхождения force-push. После работы выполните проверки из QUALITY.md и аудит приватности, затем отправьте main:

```powershell
git push origin main
git rev-parse main
git ls-remote https://gitflic.ru/project/dlarionov/math10.git refs/heads/main
git ls-remote github refs/heads/main
```

Все три hash должны совпасть. Отправка в два сервиса не атомарна: если один недоступен, сохраните коммит и повторите обычный push после устранения причины. Отдельный `git push github main` отправляет только в GitHub. Push в GitHub автоматически обновляет публичный сайт; успешный push ещё не подтверждает завершение публикации.

## GitHub Pages

В [настройках Pages](https://github.com/dlarionov/math10/settings/pages): Source — Deploy from a branch, Branch — main, папка — /(root). Обработка и публикация выполняются инфраструктурой GitHub, локальная сборка не нужна. Состояние доступно во вкладке Actions и настройках Pages.

Проверяйте каталог и переходы по адресу сайта после завершения публикации. Все файлы корня и доступных подпапок следует считать публичными, как и исходники репозитория. Не добавляйте личные заметки, результаты занятий и секреты. Сбор пользовательских данных в уроки не добавляется; хостинг может вести собственные технические журналы.

Официальные справки: [настройка источника Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site), [GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages).
