use research;

[
  'dcde8b3dcd8d4411a2311fa0a93ca4ca3b26d61f',
  '2fc0f1849bd0d6100719bb53f89f15fbd734157a',
  '2e3926b9489cb767b38526a3a72403087053a1d8',
  'fd9dbdfb3dc934a88b8b7505ab01db949a294a4e',
].forEach(commit => {
  let arr_of_results = db.performancetestresults.findOne({ commitsha: commit }).tests.filter(t => t.name.includes( 'p4211-line-log')).map(t => t.results)

  let sum = [0,0,0,0,0];
  arr_of_results.forEach(arr => {
    sum[0] += arr[0]
    sum[1] += arr[1]
    sum[2] += arr[2]
    sum[3] += arr[3]
    sum[4] += arr[4]
  });

  print(commit, sum);
})
