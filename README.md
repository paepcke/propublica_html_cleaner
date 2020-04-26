<h1>Splitting Propublica Facebook Ad Exports</h1>
Inputs a .csv file of Facebook ads as exported from Propublica. Splits the content into the following files:

* CSV: The message texts without HTML tags
* CSV: The entities
* CSV: The ad targets
* CSV: The metadata
* TXT: Just the ad text

The Propublica row id is a common key for the .csv files.

<h4>Usage</h4>

Simplest invocation:

`src/cleaner/clean_propublica_export.py /tmp/fbpac-ads-en-US.csv`

where /tmp/fbpac-ads-en-US.csv is the exported Facebook ads file from Propublica.

Use the `-h/--help` switches for more options. The options include the ability to separately specify the destination of each output file, and to limit the number of processed rows.

<h4>Example for message texts output file:</h4>

<pre>
id,message
hyperfeed_story_id_5c9baa3ee0ec08073500042,"BREAKING: Trump’s Department of the Interior plans to ...
hyperfeed_story_id_5c9bb2a2413852086735771,"The Mueller investigation is over...
        ...
</pre>

<h4>Example for entities output file:</h4>

<pre>
id,entity,entity_type
hyperfeed_story_id_5c9baa3ee0ec08073500042,Endangered Species Act,Organization
hyperfeed_story_id_5c9baa3ee0ec08073500042,Trump’s Department of the Interior,Organization
...
</pre>

<h4>Targets file:</h4>

<pre>
id,target,segment
23843380741530360,Activity on the Facebook Family,
23843380741530360,Gender,women
23843380741530360,Age,34 and older
23843380741530360,MinAge,34
23843380741530360,Region,the United States
hyperfeed_story_id_5c9bb4fa461731e29426627,none,none
</pre>

<h4>Metadata output file</h4>
The metadata file contains the following fields:

* id
* political
* not_political
* title
* thumbnail
* created_at
* updated_at
* lang
* images
* impressions
* political_probability
* targeting
* suppressed
* targets
* advertiser
* page
* lower_page
* targetings
* paid_for_by
* targetedness
* listbuilding_fundraising_proba

<h4>Example invocations on command line:</h4>

Example invocations:

<pre>
          clean_propublica_export.py the_propub_export.csv
</pre>

<pre>
          clean_propublica_export.py the_propub_export.csv -n 5000
</pre>

<pre>
         clean_propublica_export.py the_propub_export.csv \
                                -t /tmp/propub_msgs.csv 
                                -m /tmp/propub_metadata.csv 
                                -e /tmp/propub_entities.csv 
                                -a /tmp/propub_targets.csv 
                                -p /tmp/propub_pure_text.txt         
</pre>
If only a limited number of rows is needed, such as 100, add:

           -n 100

<h4>Installation</h4>

* Clone repository
* In virtual Python environment of your choice:
```python setup.py install```

<h4>Import of CSV Tables into MySQL</h4>

The .sql script in the Scripts directory creates a table for each of the generated .csv files, and loads the data from each .csv into its respective table.

<pre>
mysql -u username -p Propublica < [proj-root]/Scripts/propub_import_to_mysql.sql
</pre>

The paths hardwired into this script are:

* /tmp/propub_entities.csv
* /tmp/propub_msgs.csv
* /tmp/propub_metadata.csv
* /tmp/propub_targets.csv

Change to taste.
