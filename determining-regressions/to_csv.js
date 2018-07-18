// --- This file grabs the results out of the database

use research;
load('commits_in_order.js');

if(commits.length !== db.performancetestresults.count()) {
  print(commits.length, db.performancetestresults.count(), 'Should match!');
}

let commit_num = 0;
let dict = {};
dict.commitsha = [];
commits.reverse().forEach(sha => {
  // Grab the commit deets
  const commit_details = db.performancetestresults.findOne({ commitsha: sha });

  // Add sha
  dict.commitsha.push(sha);

  // Convert array of results to a dict
  commit_details.tests.forEach(test => {
    if(!dict[test.name]) {
      dict[test.name] = [];
      for(let i = 0; i < commit_num; i++) {
        dict[test.name].push('');
      }
    }

    dict[test.name].push(test.result);
  });

  // Fill in any tests that didnt have results for this commit
  Object.keys(dict).forEach(existing_key => {
    if(dict[existing_key].length !== commit_num + 1) {
      dict[existing_key].push('');
    }
  });

  if(commit_details.tests.length === 0) {
    print("no tests for", sha, commit_num);
  }

  commit_num++;
});

print('------')
print(dict["commitsha"].length)
print(db.performancetestresults.count())
print('------')

let keys = Object.keys(dict);
let header = '';
keys.forEach(key => {
  header += key + ',';
});
print(header);

for(let i = 0; i < commits.length; i++) {
  let line = '';
  keys.forEach(key => {
    let v = dict[key][i];
    line += v + ',';
  });
  print(line);
}
