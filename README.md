<h1>Splitting Propublica Facebook Ad Exports</h1>
Inputs a .csv file of Facebook ads as exported from Propublica. Splits the content into three .csv files:

* The message texts without HTML tags
* The entities
* The metadata

The Propublica row id is a common key for the three files.

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

<h4>Example invocation on command line:</h4>

         clean_propublica_export.py the_propub_export.csv \
                                   /tmp/propub_messages.csv \
                                   /tmp/propub_entities.csv \
                                   /tmp/propub_metadata.csv

If only a limited number of rows is needed, such as 100, add:

           -n 100

<h4>Installation</h4>

* Clone repository
* In virtual Python environment of your choice:
```python setup.py install```
