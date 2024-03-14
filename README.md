# Activity Metrics

Overview
--------
Activity metrics is a tool that can be used to analyze and display personal activity statistics. The app works by parsing daily log files that are written with a simple formatting style. The parsed data can then be converted into spreadsheets (e.g. timesheets), charts, and other useful formats such as custom textual and graphical data displays.

For installation & usage, you can navigate to the [installation](#Installation) section at the bottom, otherwise keep reading for a simple overview of the system.

### Basics

- A log is a  **.txt** file that holds the entries for a particular day.
- An example entry could be `- 8am 10m breakfast & coffee`.
- An entry always starts on it's own line with a hyphen.
- There are no limits for the number of entries or files for a day.
- All logs (including their parent directories) are stored in the main `logs/` directory.

#### File Names & Location
In the above example, let's assume the date for the entry was **Jan 1, 2024**. Here are the basic rules:

- The log file would be named with the two-digit date number and a .txt extension: i.e. `01.txt`.
- Optional custom text after the date number is allowed (e.g. `01custom-text.txt`).
- The log would be inside the proper `YYYY/MM/` directory, in this case: `2024/01/01.txt`.
- And finally, the full path for the log would be: `../logs/2024/01/01.txt`.

#### Additional Options: Full Date Log Files
- For utility reasons, log files are also allowed to be named in the `YYYY-MM-DD` format<sup>[1](#n1) [2](#n2)</sup>.
- For example: `2024-01-01.txt` or `2024-01-01custom-text.txt` would be valid full date logs.
- Since their name already includes the year & month, full date logs can be stored anywhere within `logs/`.

Valid location structure example:

```
../logs/
  - 2024/
    - 01/
      - 01.txt
      - 02.txt
      - 02-finance.txt
    - 02/
  - 2023/
    - 2023-12-31-fitness.txt
    - 08/
    - 12/
      - 16LSATstudy.txt 
```

Additionally data can also be imported from other tracking services such as Todoist, Garmin, Apple Health, Samsung Health, Financial Services, and more. Data can also be read directly from the API's of those tracking services.

**Common Categories for Activity Metrics:**

* Work
* Finances
* Academics
* Projects
* Fitness
* Nutrition
* Lifestyle

<h2 id="Installation"><small>Installation</small></h2>

1. Clone `activity-metrics/` into your local installation directory.

    ```bash
    git clone https://github.com/ryt/activity-metrics.git
    ```

2. Next create a directory named `Metrics` or something similar in your Documents and create the following 2 directories in it: `gen` and `logs`.

    You can choose whatever name you want for the main folder but we'll use "Metrics" for this example. `gen/` will be used for generated files and `logs/` will be used to store log files.

    ```bash
    mkdir Metrics && cd Metrics
    ```

    ```bash
    mkdir gen logs
    ```

3. Finally, create a symbolic link for `analyze.py` on the same level as the directories you just created. The example command is shown below. Replace `{install}` with your local installation directory:
    
    ```bash
    ln -s {install}/activity-metrics/analyze.py  Metrics/analyze
    ```

    The structure of the link and directories should look something like this:
    
    ```bash
    Metrics/
      - analyze
      - gen/
      - logs/
    ```
4. Now you can run the command `./analyze` from inside the `Metrics/` directory. Generated files will be stored inside `gen/` and your logs will be read and parsed from the `logs/`. Use `./analyze help` for the help manual.

    The utility script can be run as `./analyze utility`. Use `./analyze utility help` for the utility help manual.


<h2><small>Inspirations</small></h2>

List of inspirations for this project:

* "[Deep Habits: Should You Track Hours or Milestones?](https://calnewport.com/deep-habits-should-you-track-hours-or-milestones/)", *Article by Cal Newport, Author & Assoc. Prof. of CS @ Georgetown University*
* "[The Personal Analytics of My Life](https://web.archive.org/web/20140608105232/http://www.wired.com/2012/03/opinion-wolfram-life-analytics/all/)", *Op-Ed by Stephen Wolfram, Founder & CEO of Wolfram Research*
* "[My productivity app is a never-ending .txt file](https://jeffhuang.com/productivity_text_file/)", *Article by Jeff Huang, Researcher & Assoc. Prof. of CS @ Brown University*
* [The Complete Guide to Deep Work](https://todoist.com/inspiration/deep-work), *Guide by Todoist / Doist, Company Specializing in Productivity Tools*


<h2><small>Notes</small></h2>

1. <i id="n1"></i> [ISO 8601 Format](https://en.wikipedia.org/wiki/ISO_8601)
2. <i id="n2"></i> [XKCD 1179](https://xkcd.com/1179/)


<h2><small>License</small></h2>
<small>Copyright &copy; 2024 Ray Mentose.</small>
