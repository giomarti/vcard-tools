# vcardtools
Command line tools for splitting and merging vCard files.

There are a lot of tutorials for setting up contact servers and syncing -- but few cover the most basic step we need to take.

_Getting our vCards into a sensible shape where we can use them._

Thus far there are two operations available in vcardtools:
- splitting giant .vcf files into lots of little ones with nice names
- **and**
- merging little .vcf files two at a time with interactive prompting

##Installation
`pip install vcardtools`

##vcardtool split --help
```bash
$ vcardtool split -h
usage: vcardtool split [-h] [--pretend] [--filename_charset {utf-8,latin-1}]
                       [--output_dir OUTPUT_DIR]
                       vcard_file

positional arguments:
  vcard_file            A multi-entry vCard to split.

optional arguments:
  -h, --help            show this help message and exit
  --pretend             Print summary but do not write files
  --filename_charset {utf-8,latin-1}
                        Restrict filenames to character set
  --output_dir OUTPUT_DIR
                        Write output files in provided directory
```

##vCard Split Sample Usage
`vcardtool split --output_dir <new contacts directory> everyone-you-ever-met.vcf`


## Notes about split filenames
- By default the .vcf files are written into the current directory, there can be a lot of them, you have been warned.
- File names take the form `lastname_firstname.vcf` or as the fields are available. 
- Fall back is to use the login section of an email address.
- If insufficient data is available to make a name a warning is shown and the record is skipped.
- If file names become duplicated say 'john.vcf'; *all* the John's get an extension so you can easily identify them later: `['john-1.vcf', 'john-2.vcf', ...]`  (View them with something like: `ls *-?.vcf`)
- By default filenames are forced into the latin-1 character set.  So you'll find some of your friends with non-ascii vCard names by their email login instead.  (if you want to change this set `--filename_charset=utf-8` ... and use Python 3, see Issues above to track progress on the Python 2.7 fix)
- If you cancel midway or anything goes wrong -- feel free to re-run it.  `vcardtool split` skips writing files with the same name in the given output directory so you can safely re-run to get those last 5 vCards at the end created.


##vcardtool merge --help
```bash
$ vcardtool merge -h
usage: vcardtool merge [-h] [--outfile [OUTFILE]] vcard_files vcard_files

positional arguments:
  vcard_files          Two vCard files to merge

optional arguments:
  -h, --help           show this help message and exit
  --outfile [OUTFILE]  Write merged vCard to file

vcardtool merge john-1.vcf john-2.vcf
```

##vCard Merge Sample Usage
`$ vcardtool merge john-1.vcf john-2.vcf`
<output editted for brevity>

In the even of a conflict you'll see something like:
```
Please select one of the following options for field "label"
[ 1 ] "[<LABEL{'TYPE': ['WORK']}100 Waters Edge Baytown, LA 30314 United States of America>,
        <LABEL{'TYPE': ['HOME']}42 Plantation St. Baytown, LA 30314 United States of America>]"
[ 2 ] "[<LABEL{'TYPE': ['HOME']}42 Plantation St. Baytown, LA 30314 United States of America>]"
option> 5
option> 1
```

And then hopefully victory.
```
BEGIN:VCARD
VERSION:3.0
ADR;TYPE=HOME:;;42 Plantation St.;Baytown;LA;30314;United States of America
ADR;TYPE=WORK:;;100 Waters Edge;Baytown;LA;30314;United States of America
EMAIL;TYPE=PREF,INTERNET:forrestgump@example.com
FN:Forrest Gump
LABEL;TYPE=WORK:100 Waters Edge\nBaytown\, LA 30314\nUnited States of Ameri
 ca
LABEL;TYPE=HOME:42 Plantation St.\nBaytown\, LA 30314\nUnited States of Ame
 rica
N:Gump;Forrest;;Mr.;
PHOTO;TYPE=JPEG;VALUE=URL:http://www.example.com/dir_photos/my_photo.gif
REV:2008-04-24T19:52:43Z
TEL;TYPE=HOME,VOICE:(111) 555-5555
TEL;TYPE=WORK,VOICE:(111) 555-1212
TEL;TYPE=HOME,VOICE:(404) 555-1212
TITLE:Shrimp Man
END:VCARD
```

By default the merge command writes to stdout although it can be directed to a file with `--outfile shiny_new.vcf`.
