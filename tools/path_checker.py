import optparse
import os
import re 
import sys

from BeautifulSoup import BeautifulSoup as Parser

total_count = 0
email_errors = []
path_errors = []

def main(_argv, _stdout, _stderr):
    options, args = parse_args()
    repo_dir = args[0]
    
    global total_count
    global email_errors
    global path_errors
     
    total_count = 1
    email_errors = []
    path_errors = []
    
    for root, dirs, files in os.walk(repo_dir):
        print 'Checking files in ' + root + '...'
        
        DIRS_TO_SKIP = ('.git', '.hg', 'data', 'support', 'test-plan', 'fonts', 'work-in-progress', 'vendor-imports', 'w3ctestlib', 'tools')
        for d in DIRS_TO_SKIP:
            if d in dirs:
                dirs.remove(d)
                
        for filename in files:
            if filename.startswith('.') or filename.endswith('.pl') or filename.endswith('.png') or filename.endswith('disabled-due-to-limitations-in-the-build-system') or filename.endswith('.pm') or filename == 'index.html' or filename == 'index.xht':
                continue
            
            find_support_files(root, filename)   
        
    
    i = 1
    for error in path_errors:
        print 'Path error ' + str(i) +': '+ error[0] + ' not found from ' + error[1]
        i += 1
        
    i = 1
    for error in email_errors:
        print 'Email error ' + str(i) +': '+ error[0] + ' in '+ error[1]
        i += 1
    
    print 'Checked ' + str(total_count) + ' files'
    print 'Found ' + str(len(path_errors)) + ' path errors'
    print 'Found ' + str(len(email_errors)) + ' email errors'
    
    
def find_support_files(root, filename):
    support_files = []
    global total_count
    global email_errors
    global path_errors
    
    fullpath = os.path.join(root, filename)
   
    #print 'Opening ' + fullpath + '...'
    doc = Parser(open(fullpath))

    if doc is None:
        return support_files

    total_count += 1
    
    elements_with_src_attributes = doc.findAll(src=re.compile('.*'))
    elements_with_href_attributes = doc.findAll(href=re.compile('.*'))
    
    url_pattern = re.compile('url\(.*\)')
    urls = []
        
    for url in doc.findAll(text=url_pattern):
        url = re.search(url_pattern, url)
        url = re.sub('url\([\'\"]?', '', url.group(0))
        url = re.sub('[\'\"]?\).*', '', url)
        urls.append(url)

    src_paths = [src_tag['src'] for src_tag in elements_with_src_attributes]
       
    spec_links = []
    author_links = []
    reviewer_links = []
    match_links = []
    stylesheet_links = []
    other_links = []
    
    for href_tag in elements_with_href_attributes:
        
        try:
            rel_tag = href_tag['rel']
        except KeyError:
            other_links.append(href_tag['href'])
            continue
       
        if rel_tag == 'author':
            author_links.append(href_tag['href'])
        elif rel_tag == 'reviewer':
            reviewer_links.append(href_tag['href'])
        elif rel_tag == 'match':
            match_links.append(href_tag['href'])
        elif rel_tag == 'mismatch':
            match_links.append(href_tag['href'])
        elif rel_tag == 'help':
            spec_links.append(href_tag['href'])
        elif rel_tag == 'stylesheet' or rel_tag == 'alternate stylesheet' or rel_tag == 'Stylesheet':
            stylesheet_links.append(href_tag['href'])
        elif rel_tag == 'alternate' or rel_tag == 'bookmark':
            other_links.append(href_tag['href'])
        else:
            other_links.append(href_tag['href'])
            
    paths = src_paths + match_links + urls
    
    for path in paths:
        #if not(path.startswith('http:')) and not(path.startswith('mailto:')) and not(path.startswith('/resources/testharness')) and not(path.startswith('data')) and not(path.startswith('https:')) and not(path.startswith('/delay')) and not(path.startswith('javascript')):
        if is_actual_filepath(path):
            support_files.append(path)
            
    for support_file in support_files:
        support_path = os.path.join(root, support_file)
        if not os.path.exists(support_path):
            
            # Check if it's an email address
            email_pattern = re.compile('.+@.*\..*')
            match = re.search(email_pattern, support_path)
            if match is not None:
                email_errors.append( (support_file, fullpath))
            else:
                path_errors.append( (support_file, fullpath))      
    
def is_actual_filepath(path):
    prefixes = ['http', 'https', 'mailto:', '/resources/testharness', 'data', 'delay', 'javascript']
    for prefix in prefixes:
        if path.startswith(prefix):
            return False
        
    return True
        
    
def parse_args():
    parser = optparse.OptionParser(usage='usage: %prog repo_path')
    
    options, args = parser.parse_args()
    if len(args) != 1:
        parser.error('Incorrect number of arguments')
    
    return options, args


sys.exit(main(sys.argv[1:], sys.stdout, sys.stderr))