const { join } = require('path')
const QuickgRPC = require('quick-grpc')

async function go () {
  const { filesync } = await new QuickgRPC({
    host: 'localhost:9102',
    basePath: join(__dirname, '..', '..', 'filesync')
  })

  let fs = await filesync()
  fs.info(undefined, function (err, data) {
    if (err) throw err
    console.log(JSON.stringify(data, null, 2))
  })
}

go()
