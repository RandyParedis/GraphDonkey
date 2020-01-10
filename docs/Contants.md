# Constants
Even though `GraphDonkey` is widely customizable, there are a predefined set of
constants that exist throught the system. These cannot be changed and are used on
numerous occasions. If you are [making a plugin](Plugins.md), you might want to use
some of them to link with the overall system settings.

These constants are located in the `main.extra.Contants` module, which is ideally
imported as follows to prevent collisions.
```
from main.extra import Constants
```

It contains the following values:

