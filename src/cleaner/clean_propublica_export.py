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
import re
import shutil
import signal
from subprocess import CalledProcessError
import subprocess
import sys
import tempfile

class PropublicaCleaner(object):
    '''
    Inputs a .csv file of Facebook ads as exported
    from Propublica. Splits the content into four
    .csv files:

      o The message texts without HTML tags.
      o The entities
      o The metadata
      o The ad targets

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
	
	Example for ad targets:
	    id,target,segment
	    hyperfeed_story_id_5c9baa3ee0ec08073500042,"Activity on the Facebook Family",Women
	    hyperfeed_story_id_5c9baa3ee0ec08073500042,Age,34 and older
	    
		          
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
    
    # Variables needed outside of instance
    # to save work when user hits cnt-C:

    OUT_FDS = {}

    #------------------------------------
    # Constructor
    #-------------------

    def __init__(self, 
                 csv_in_file,
                 metadata_outfile=None,
                 entities_outfile=None,
                 text_outfile=None,
                 targets_outfile=None,
                 pure_text_outfile=None,
                 num_rows=None
                 ):
        '''
        Constructor
        '''
        # The number of rows we are to process (None means 'all'):
        self.num_rows = None if num_rows is None else int(num_rows)
        
        # Get paths to the outfiles; either keeping what was
        # passed in, or deriving file names from the csv_in_file:
        out_paths = self.generate_outfile_paths(csv_in_file,
                                                metadata_outfile,
                                                entities_outfile,
                                                text_outfile,
                                                targets_outfile,
                                                pure_text_outfile
                                                )
        
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

            entities_out_fd = open(out_paths['entities_outfile'], 'w')
            metadata_out_fd = open(out_paths['metadata_outfile'], 'w')
            targets_out_fd  = open(out_paths['targets_outfile'], 'w')

            # For cleanup after a possible cnt-C
            PropublicaCleaner.OUT_PATHS = out_paths
            PropublicaCleaner.OUT_FDS = {'text_out_fd'     : text_out_fd,
                                         'entities_out_fd' : entities_out_fd,
                                         'metadata_out_fd' : metadata_out_fd,
                                         'targets_out_fd'  : targets_out_fd
                                         }
            
            with open(csv_in_file, newline='') as csv_in_fd:
                
                print("Start splitting to out files...")
                # Do the work:
                self.output_clean_csv(csv_in_fd, PropublicaCleaner.OUT_FDS)
    
            tmp_file_name = text_out_fd.name
            text_out_fd.close()
            
            # Use SED to remove the HTML <p></p> tags left
            # over in the messages texts:
            self.clean_textfile(tmp_file_name, text_outfile)
            
        finally:
            entities_out_fd.close()
            metadata_out_fd.close()
            
        # Create one last table: the pure text table,
        # without an ID key, for pure text processing.
        
        self.create_pure_text_table(out_paths)
        

    #------------------------------------
    # output_clean_csv
    #-------------------

    def output_clean_csv(self, csv_in_fd, out_fd_dict):
        
        # For reading the original Propublica export:
        reader = csv.DictReader(csv_in_fd)
        # Get Propublica column header: 
        col_headers = reader.fieldnames.copy()
        # We will not output the html code:
        col_headers.remove('html')
        col_headers.remove('entities')
        col_headers.remove('message')
        col_headers.remove('targets')
        
        metadata_out_writer = csv.DictWriter(out_fd_dict['metadata_out_fd'],col_headers)
        metadata_out_writer.writeheader()
        
        entities_writer = csv.DictWriter(out_fd_dict['entities_out_fd'],
                                         ['id', 'entity', 'entity_type'])
        entities_writer.writeheader()
        
        text_writer = csv.DictWriter(out_fd_dict['text_out_fd'], ['id', 'message'])
        text_writer.writeheader()
        
        targets_writer = csv.DictWriter(out_fd_dict['targets_out_fd'], ['id','target','segment'])
        targets_writer.writeheader()

        rows_processed = 0
        total_rows_processed = 0
        
        html_rm_pat = re.compile(r'<[^>]+>')
        
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
                
            
            # Write the plain text column's output to the text csv file:
            txt_output = {'id' : row_id, 'message' : row_dict['message']}
            text_writer.writerow(txt_output)
            
            # Targeting is also a JSON array, and goes to 
            # a different table:
            id_only_dict = OrderedDict({'id': row_id})
            try:
                targets = json.loads(row_dict['targets'])
                if len(targets) == 0:
                    targets_writer.writerow({'id' : row_id,
                                             'target' : 'none',
                                             'segment' : 'none'
                                             })
                else:
                    for target_dict in targets:
                        all_targets = id_only_dict.copy()
                        # Join the id and each entity dict
                        all_targets.update(target_dict)                
                        targets_writer.writerow(all_targets)

            except json.decoder.JSONDecodeError:
                targets = targets_writer.writerow({'id' : row_id,
                                                   'target' : 'not specified',
                                                   'segment' : 'not_specified'
                                                })
                
            # Don't want to save the HTML, entities, msg text, or targets
            # in the metadata csv:
            del(row_dict['html'])
            del(row_dict['message'])
            del(row_dict['entities'])
            del(row_dict['targets'])
            
            # The targeting and targetings columns are
            # HTML: get plain text:
            if len(row_dict['targeting']) > 0:
                row_dict['targeting'] = html_rm_pat.sub('', row_dict['targeting'])
            if len(row_dict['targetings']) > 0:
                row_dict['targetings'] = html_rm_pat.sub('', row_dict['targetings'])
            
            metadata_out_writer.writerow(row_dict)

            # Another row processed:
            rows_processed += 1
            if rows_processed >= self.REPORT_EVERY:
                total_rows_processed += rows_processed
                print(f"Processed {total_rows_processed} rows")
                rows_processed = 0
        
        # Announce final row count:
        total_rows_processed += rows_processed
        print(f"Processed total of {total_rows_processed} rows.")
        
    #------------------------------------
    # clean_textfile
    #-------------------
    
    @classmethod
    def clean_textfile(cls, tmp_file_name, text_outfile):
        '''
        Takes path to a file with the ad messages.
        Removes any lingering HTML tags, and writes
        the result to text_outfile. Then removes the
        source file.
        
        If error, prints message, and moves the source
        file to text_outfile.
        
        Must be a class method, because the cnt-C handler
        must be able to call it.
        
        @param tmp_file_name: path to file with contaminated message texts
        @type tmp_file_name: str
        @param text_outfile: destination path for the cleaned output,
            or the contaminated file, if cleaning fails
        @type text_outfile: str
        '''
        
        print(f"Removing stray par tags from messages texts (SEDing from {tmp_file_name} to {text_outfile}...)")

        shell_cmd = f"sed -e 's/<[^>]*>//g' {tmp_file_name} > {text_outfile}"
        try:
            subprocess.run(shell_cmd, check=True, shell=True)
        except CalledProcessError as e:
            print(f"Could not remove paragraph tags from messages file: {repr(e)}")
            # Just move the message tmp file to its final
            # destination:
            print(f"Moving {tmp_file_name} to {text_outfile}")

            shutil.move(tmp_file_name, text_outfile)
        else:
            print(f"Removing {tmp_file_name}")
            # The HTML tag cleanup worked.
            os.remove(tmp_file_name)

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
      
      
    #------------------------------------
    # generate_outfile_paths
    #-------------------
          
    def generate_outfile_paths(self,
                               csv_in_file,
                               metadata_outfile,
                               entities_outfile,
                               text_outfile,
                               targets_outfile,
                               pure_text_outfile
                               ):
        
        out_dir = os.path.dirname(csv_in_file)
        
        (in_file_root,_extension) = os.path.splitext(csv_in_file)
        if metadata_outfile is None:
            metadata_outfile = os.path.join(out_dir, in_file_root + '_metadata.csv')
        if entities_outfile is None:
            entities_outfile = os.path.join(out_dir, in_file_root + '_entities.csv')
        if text_outfile is None:
            text_outfile = os.path.join(out_dir, in_file_root + '_text.csv')
        if targets_outfile is None:
            targets_outfile = os.path.join(out_dir, in_file_root + '_targets.csv')
        if pure_text_outfile is None:
            pure_text_outfile = os.path.join(out_dir, in_file_root + '_pure_text.csv')
        
        return {'metadata_outfile' : metadata_outfile,
                'entities_outfile' : entities_outfile,
                'text_outfile'     : text_outfile,
                'targets_outfile'  : targets_outfile,
                'pure_text_outfile': pure_text_outfile
                }

    #------------------------------------
    # create_pure_text_table
    #-------------------
    
    def create_pure_text_table(self, outfile_dict):
        pure_txt_outfile = outfile_dict['pure_text_outfile']
        msgs_infile      = outfile_dict['text_outfile']
        shell_cmd = f"tail -n +2 {msgs_infile} | cut -d ',' -f 2 > {pure_txt_outfile}"
        print("Creating pure-text file...")
        try:
            subprocess.run(shell_cmd, check=True, shell=True)
        except CalledProcessError as e:
            print(f"Could not create pure text file from messages csv file: {repr(e)}")
        else:
            print("Done creating pure-text file.")

# ------------------------------ Cnt-C Signal Handler -------------

def signal_handler(signal, frame):
        print('Abort in response to Ctrl+C...')
        print('Saving partially done work ...')
        
        tmp_file_name = PropublicaCleaner.OUT_FDS['text_out_fd'].name
        for fd_key in PropublicaCleaner.OUT_FDS.keys():
            PropublicaCleaner.OUT_FDS[fd_key].close()
        
        # Put whatever message texts have been done
        # through the SED cleaner, and to the final
        # out file:
        PropublicaCleaner.clean_textfile(tmp_file_name, PropublicaCleaner.OUT_PATHS['text_outfile'])
        
        print('Done saving partial work')
        
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
    parser.add_argument('-t', '--textoutfile',
                        help="Destination each row's advertising text information; default: stdout")
    parser.add_argument('-m', '--metadata_outfile',
                        help="Destination of each row's metadata")
    parser.add_argument('-e', '--entities_outfile',
                        help="Destination each row's csv entity information")
    parser.add_argument('-a', '--targetsoutfile',
                        help="Destination each row's csv targets information")
    parser.add_argument('-p', '--puretextoutfile',
                        help="Destination of text file with no row info at all (for txt processing)")

    
    parser.add_argument('csv_in_file',
                        help='Propublica ad exported .csv file')

    args = parser.parse_args();
    
    csv_in_file = args.csv_in_file
    if not os.path.exists(csv_in_file):
        print(f"CSV file {csv_in_file} not found; quitting")
        sys.exit()
    
    PropublicaCleaner(csv_in_file,
                      args.metadata_outfile, 
                      args.entities_outfile, 
                      args.textoutfile,
                      args.targetsoutfile,
                      args.puretextoutfile,
                      args.numrows
                      )
