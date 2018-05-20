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

def run_lizard(file_paths, root_path)
    highest_complexity = 0
    file_paths.each do |file_path|
        i = lizard.analyze_file(root_path+'/'+file_path)
        i.function_list.each do |func_info|
            cc = func_info.__dict__['cyclomatic_complexity']
            if cc > highest_complexity
                highest_complexity = cc
            end
        end
    end
    return highest_complexity
end

def get_fail_history(file_paths)
    most_fails = 0
    total_fails = 0
    file_paths.each do |path|
        if $fail_history[path] > most_fails
            most_fails = $fail_history[path]
        end
        total_fails += $fail_history[path]
    end

    #TODO most or total?
    return total_fails
end

def update_fail_history(file_paths)
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
    diff = g.diff('HEAD', 'HEAD~1')
    flux = diff.insertions + diff.deletions
    highest_cc = 0 # TODO run_lizard(files_changed, root_path)
    history = get_fail_history(files_changed)
    return highest_cc, flux, history
end

def travis_stuff(repo_name, g)
    repo = Travis::Repository.find(repo_name)

    puts "Pulling builds, this may take a bit..."
    # If we did repo.each_build, this would go fast, but iterate in reverse
    CSV.open('results.csv', 'w') do |csv|
        csv << ['Build State', 'Cyclomatic_complexity', 'Flux', 'Fail History', 'Total Failures', 'History/Number builds', 'History / Number failed builds', 'Build Number', 'Commit SHA']
        repo.builds.reverse_each do |build|
            commit = build.commit
            begin
                g.checkout(commit.sha)
                files_changed = get_changed_file_paths(g)
                cc, flux, history = analyze_commit(g, '/tmp/thesis-checkout/'+repo_name, files_changed)
                history_over_total = history/build.number.to_f
                history_over_fails = $total_failures != 0 ? history/$total_failures.to_f : 1
                puts "#{build.number}: #{build.state}, #{cc}, #{flux}, #{history}, #{$total_failures}, #{history_over_total}, #{history_over_fails}, #{commit.sha}"
                csv << [build.state, cc, flux, history, $total_failures, history_over_total, history_over_fails, build.number, commit.sha]
                if build.state == 'failed'
                    update_fail_history(files_changed)
                end
            rescue Git::GitExecuteError => _
                #puts "Unable to checkout #{commit.sha} from #{build.number}"
            end
        end
    end

end

def open_git(url, repo_name)
    g = nil
    unless File.directory?('/tmp/thesis-checkout/'+repo_name)
        g = Git.clone(
            url,
            repo_name,
            :path => '/tmp/thesis-checkout',
        )
    else
        g = Git.open('/tmp/thesis-checkout/'+repo_name)
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
