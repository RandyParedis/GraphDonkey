# Create an executable for GraphDonkey on Linux
pyinstaller __main__.py -n GraphDonkey \
  --add-data ./vendor/:vendor/ \
  --add-data README.md:. -y