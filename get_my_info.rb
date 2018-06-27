#!/bin/ruby
require 'travis'
require 'git'
require 'csv'
require 'pycall/import' # "lizard" is a python library!
include PyCall::Import
pyimport :lizard

#TODO remove
require 'pry' #to drop in, put 'binding.pry'

$total_failures = 0
$fail_history = Hash.new(0)

def ranges_overlap(x1, x2, y1, y2)
    # returns true if the given ranges overlap
    #  ie 1,3 and 2,4 overlap, but 1,3 and 5,6 do not
    return x1 <= y2 && y1 <= x2
end

def check_header(header_line, fn_start, fn_end)
    # If we get here, it means we have the header string.
    # Now, we calculate the start and end lines in the current file
    # An example hunk header looks like this:
    # @@ -72,7 +72,7 @@ describe('TodoStore', function() {
    line_and_size = header_line.split(' ')[2].split(',')
    line_and_size[0][0] = '' # Remove the - or + symbol
    start_line = line_and_size[0].to_i
    end_line = start_line + line_and_size[1].to_i

    return ranges_overlap(start_line, end_line, fn_start, fn_end)
end

def diff_touched_lines(diff, file_path, fn_start, fn_end)
    ##
    # Getting which lines were edited requires grabbing the diff hunk
    # header, then parsing into start and end lines
    # There can be more than one header per file
    ##

    # Used to track if we are in the right file section within the diff
    looking_for_headers = false
    ## First, we find the header line
    diff.patch.each_line do |line|
        # Check if this is a header, if we are in the block of changes
        # for the given file
        if looking_for_headers and /@@\ .*\ .*\ @@/.match(line)
            # Check to see if this header tells us that our functions changed
            if check_header(line, fn_start, fn_end)
                return true
            end
        end

        begin
            if looking_for_headers and /\+\+\+\ [a,b]/.match(line)
                # If we already found the file we are looking for,
                # and we find another file marker, it's over
                break
            end

            # If we find a file header and it is the file we want
            if /\+\+\+\ [a,b]/.match(line) and line.include? file_path
                looking_for_headers = true
            end
        rescue ArgumentError
            puts 'Unable to parse line as valid ASCII. Are you running in tmux?'
        end
    end

    return false
end

def lizard_can_parse(file_path)
    parseable_extensions = [
        'c',
        'h',
        'cpp',
        'hpp',
        'java',
        'cs',
        'js',
        'm',
        'mm',
        'swift',
        'py',
        'rb',
        'ttcn',
        'php',
        'scala',
        'tscn',
        ]
    match = /\.([0-9a-z]+$)/.match(file_path)
    if match == nil
        return false
    end
    captures = match.captures
    if captures.length == 0
        return false
    end

    return parseable_extensions.include? captures[0].downcase
end

def run_lizard(file_paths, root_path, diff)
    ##
    # This function runs the lizard tool (https://github.com/terryyin/lizard)
    # on the given file paths.
    #
    # This tool can calculate number of lines of code, cyclomatic
    # complexity, and a couple other metrics.
    #
    # The lizard tool runs on files, and so it returns metrics for functions
    # that we may not have touched. We use the diff to determine
    # whether we actually edited a given function. That way we ignore
    # functions that lizard analyzes but we dont care about
    ##
    highest_complexity = 0
    total_complexity = 0
    file_paths.each do |file_path|
        # Filter out anything lizard cant parse
        if not lizard_can_parse(file_path)
            next
        end

        # Figure out which lines we actually touched in our diff.
        lizard_analysis = lizard.analyze_file(root_path+'/'+file_path)
        lizard_analysis.function_list.each do |func_info|

            cc = func_info.__dict__['cyclomatic_complexity']
            fn_start = func_info.__dict__['start_line']
            fn_end = func_info.__dict__['end_line']

            # Did we actually touch this function?
            if diff_touched_lines(diff, file_path, fn_start, fn_end)
                total_complexity += cc
                # Is this complexity higher than our current highest?
                if cc > highest_complexity
                    highest_complexity = cc
                end
            end
        end
    end
    return highest_complexity, total_complexity
end

def get_fail_history(file_paths)
    ##
    # This pulls the "fail history" value for the given paths
    ##
    most_fails = 0
    total_fails = 0
    file_paths.each do |path|
        if $fail_history[path] > most_fails
            most_fails = $fail_history[path]
        end
        total_fails += $fail_history[path]
    end

    #TODO highest failing file or total fails over all files?
    return total_fails
end

def update_fail_history(file_paths)
    ##
    # Increment the fail history values for the given
    # file paths
    ##
    file_paths.each do |path|
        $fail_history[path] += 1
    end
    $total_failures += 1
end

def get_changed_file_paths(g)
    diff = g.diff('HEAD', 'HEAD~1')
    files_changed = []
    diff.each do |file_diff|
        files_changed.push(file_diff.path)
    end
    return files_changed
end


def analyze_commit(g, root_path, files_changed)
    ##
    # Calculate the different metrics for each file
    ##
    diff = g.diff('HEAD', 'HEAD~1')
    flux = diff.insertions + diff.deletions
    highest_cc, total_cc = run_lizard(files_changed, root_path, diff)
    history = get_fail_history(files_changed)
    return highest_cc, total_cc, flux, history
end

def git_checkout_commit(g, sha)
    begin
        begin
            g.checkout(sha)
        rescue Git::GitExecuteError => _
            g.reset_hard
            g.checkout(sha)
        end
    rescue
        puts "Unable to checkout #{sha}"
        return false
    end
    return true
end

def travis_stuff(repo_name, g)
    repo = Travis::Repository.find(repo_name)

    puts "Pulling builds, this may take a bit..."
    # If we did repo.each_build, this would go fast, but iterate in reverse
    CSV.open(repo_name.split('/')[1] + '.csv', 'w') do |csv|
        csv << ['Build State', 'Highest Cyclomatic complexity', 'Total CC', 'Flux', 'Fail History', 'Total Failures', 'History/Number builds', 'History / Number failed builds', 'Build Number', 'Commit SHA']
        repo.builds.reverse_each do |build|
            commit = build.commit
            if not git_checkout_commit(g, commit.sha)
                next
            end
            files_changed = get_changed_file_paths(g)
            highest_cc, total_cc, flux, history = analyze_commit(g, 'checkouts/'+repo_name, files_changed)
            history_over_total = history/build.number.to_f
            history_over_fails = $total_failures != 0 ? history/$total_failures.to_f : 1
            puts "#{build.number}: #{build.state}, #{highest_cc}, #{total_cc}, #{flux}, #{history}, #{$total_failures}, #{history_over_total}, #{history_over_fails}, #{commit.sha}"
            csv << [build.state, highest_cc, total_cc, flux, history, $total_failures, history_over_total, history_over_fails, build.number, commit.sha]
            if build.state == 'failed'
                update_fail_history(files_changed)
            end
        end
    end

end

def open_git(url, repo_name)
    g = nil
    unless File.directory?('checkouts/'+repo_name)
        g = Git.clone(
            url,
            repo_name,
            :path => 'checkouts',
        )
    else
        g = Git.open('checkouts/'+repo_name)
        g.fetch
    end
    return g
end


def main(repo_name)
    unless repo_name
        puts 'You must provide the repo name/group (ex: facebook/react)'
        return 1
    end

    github_url = 'https://github.com/' + repo_name
    puts "Running on " + github_url

    g = open_git(github_url, repo_name)
    travis_stuff(repo_name, g)

    return 0
end

exit(main(ARGV[0]))
