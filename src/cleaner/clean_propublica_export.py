#!/usr/bin/env python

'''
Created on Apr 24, 2020

@author: paepcke
'''
from _collections import OrderedDict
import argparse
import csv
import json
import os
from subprocess import CalledProcessError
import subprocess
import sys
import tempfile
import shutil
import signal

class PropublicaCleaner(object):
    '''
    Inputs a .csv file of Facebook ads as exported
    from Propublica. Splits the content into three 
    .csv files:

      o The message texts without HTML tags.
      o The entities
      o The metadata

    The Propublica row id is a common key for the three
    files.

    Example for message texts:
		 id,message
		 hyperfeed_story_id_5c9baa3ee0ec08073500042,"BREAKING: Trump’s Department of the Interior plans to ...
		 hyperfeed_story_id_5c9bb2a2413852086735771,"The Mueller investigation is over...
		          ...
    Example for entities:
		id,entity,entity_type
		hyperfeed_story_id_5c9baa3ee0ec08073500042,Endangered Species Act,Organization
		hyperfeed_story_id_5c9baa3ee0ec08073500042,Trump’s Department of the Interior,Organization
		          ...
		          
	The metadata file contains the following fields:
	
        id,political,not_political,title,thumbnail,created_at,
        updated_at,lang,images,impressions,political_probability,
        targeting,suppressed,targets,advertiser,page,lower_page,
        targetings,paid_for_by,targetedness,listbuilding_fundraising_proba	

    Example invocation on command line:
    
         clean_propublica_export.py the_propub_export.csv \
                                   /tmp/propub_messages.csv \
                                   /tmp/propub_entities.csv \
                                   /tmp/propub_metadata.csv
                                   
    If only a limited number of rows is needed, such as 100, add:
    
           -n 100 
    
    '''

    # Intervals when to report number of rows
    # processed. Units: number of rows:

    REPORT_EVERY = 10000
    
    #------------------------------------
    # Constructor
    #-------------------

    def __init__(self, 
                 csv_in_file,
                 metadata_outfile,
                 entities_outfile,
                 text_outfile,
                 num_rows=None
                 ):
        '''
        Constructor
        '''
        # The number of rows we are to process (None means 'all'):
        self.num_rows = None if num_rows is None else int(num_rows)
        
        # Prepare the csv module to accept very long
        # field values:
        self.adjust_csv_field_size_limit()
        
        # Open the output files:
        try:
            # Put message texts into a temp file, so we
            # can remove stray HTML tags at the end,
            # using SED, which is much faster than doing it
            # in Python:
            text_out_fd = tempfile.NamedTemporaryFile('w', delete=False)
            
            entities_out_fd = open(entities_outfile, 'w')
            metadata_out_fd = open(metadata_outfile, 'w')
            
            with open(csv_in_file, newline='') as csv_in_fd:
                
                # Do the work:
                self.output_clean_csv(csv_in_fd, 
                                      metadata_out_fd, 
                                      entities_out_fd, 
                                      text_out_fd)

    
            # Use SED to remove the HTML <p></p> tags:

            tmp_file_name = text_out_fd.name
            text_out_fd.close()

            shell_cmd = f"sed -e 's/<[^>]*>//g' {tmp_file_name} > {text_outfile}"
            try:
                subprocess.run(shell_cmd, check=True, shell=True)
            except CalledProcessError as e:
                print(f"Could not remove paragraph tags from messages file: {repr(e)}")
                # Just move the message tmp file to its final
                # destination:
                shutil.move(tmp_file_name, text_outfile)
            else:
                # The HTML tag cleanup worked.
                os.remove(tmp_file_name)
            
        finally:
            entities_out_fd.close()
            metadata_out_fd.close()



    #------------------------------------
    # output_clean_csv
    #-------------------

    def output_clean_csv(self, csv_in_fd, metadata_out_fd, entities_out_fd, text_out_fd):
        
        # For reading the original Propublica export:
        reader = csv.DictReader(csv_in_fd)
        # Get Propublica column header: 
        col_headers = reader.fieldnames.copy()
        # We will not output the html code:
        col_headers.remove('html')
        col_headers.remove('entities')
        col_headers.remove('message')
        
        metadata_out_writer = csv.DictWriter(metadata_out_fd,col_headers)
        metadata_out_writer.writeheader()
        
        entities_writer = csv.DictWriter(entities_out_fd,
                                         ['id', 'entity', 'entity_type'])
        entities_writer.writeheader()
        
        text_writer = csv.DictWriter(text_out_fd, ['id', 'message'])
        text_writer.writeheader()

        rows_processed = 0
        total_rows_processed = 0
        
        # Read from the export csv file:
        for row_dict in reader:
            if self.num_rows is not None: 
                if self.num_rows <= 0:
                    break
                else:
                    self.num_rows -= 1
                
            row_id = row_dict['id']
            
            # The entities column is a JSON object.
            # Grab it, and generate rows for the 
            # entities table:
            id_only_dict = OrderedDict({'id': row_id})
            try:
                entities = json.loads(row_dict['entities'])
                for entity_dict in entities:
                    entities = id_only_dict.copy()
                    # Join the id and each entity dict
                    entities.update(entity_dict)                
                    entities_writer.writerow(entities)

            except json.decoder.JSONDecodeError:
                entities = entities_writer.writerow({'id' : row_id,
                                                     'entity' : 'not specified',
                                                     'entity_type' : 'not_specified'
                                                     })
                
            
            # Write out the text:
            txt_output = {'id' : row_id, 'message' : row_dict['message']}
            text_writer.writerow(txt_output)
            
            # Don't want to save the HTML or entities:
            del(row_dict['html'])
            del(row_dict['message'])
            del(row_dict['entities'])
            metadata_out_writer.writerow(row_dict)
            
            # Another row processed:
            rows_processed += 1
            if rows_processed >= self.REPORT_EVERY:
                total_rows_processed += rows_processed
                print(f"Processed {total_rows_processed} rows")
                rows_processed = 0

    #------------------------------------
    # adjust_csv_field_size_limit
    #-------------------
    
    def adjust_csv_field_size_limit(self):
        '''
        Propublica's CSV exports contain large fields.
        These cause csv read errors. Adjust the csv max
        field length to the max possible on this computer
        
        '''
        maxInt = sys.maxsize
        
        while True:
            # decrease the maxInt value by factor 10 
            # as long as the OverflowError occurs.
        
            try:
                csv.field_size_limit(maxInt)
                break
            except OverflowError:
                maxInt = int(maxInt/10)

# ------------------------------ Cnt-C Signal Handler -------------

def signal_handler(signal, frame):
        print('Exiting in response to Ctrl+C.')
        sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

# ----------------------------- Main ----------------

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog=os.path.basename(sys.argv[0]),
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     description="Remove html tags from Propublica advertising .csv export"
                                     )

    parser.add_argument('-n', '--numrows',
                        type=int,
                        help="Maximum number of rows to process; default: all",
                        default=None)
    parser.add_argument('csv_in_file',
                        help='Propublica ad exported .csv file')
    parser.add_argument('textoutfile',
                        help="Destination each row's advertising text information; default: stdout")
    parser.add_argument('metadata_outfile',
                        help="Destination of each row's metadata")
    parser.add_argument('entities_outfile',
                        help="Destination each row's csv entity information")

    args = parser.parse_args();
    
    csv_in_file = args.csv_in_file
    if not os.path.exists(csv_in_file):
        print(f"CSV file {csv_in_file} not found; quitting")
        sys.exit()
    
    PropublicaCleaner(csv_in_file,
                      args.metadata_outfile, 
                      args.entities_outfile, 
                      args.textoutfile,
                      args.numrows                      
                      )
