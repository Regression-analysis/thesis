#!/bin/ruby
require 'travis'
require 'git'


def travis_stuff(repo_name, g)
    repo = Travis::Repository.find(repo_name)

    repo.each_build do |build|
        commit = build.commit
        begin
            g.checkout(commit.sha)
            puts "#{build.number}: #{build.state}, #{commit.sha}"
        rescue Git::GitExecuteError => _
            puts "Unable to checkout #{commit.sha} from #{build.number}"
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
