:: Create an executable for GraphDonkey on Windows
rmdir -r .\vendor\plugins\.dependencies
pyinstaller __main__.py -n GraphDonkey ^
    --add-data ".\vendor\;.\vendor" ^
    --add-data "README.md;." ^
    -i .\vendor\icons\app.ico -yw