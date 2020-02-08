# Create an executable for GraphDonkey on Linux
rm -rf ./vendor/plugins/.dependencies
pyinstaller __main__.py -n GraphDonkey \
  --add-data ./vendor/:vendor/ \
  --add-data README.md:. -y