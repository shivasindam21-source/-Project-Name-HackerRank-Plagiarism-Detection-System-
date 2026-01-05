// const express = require("express");
// const { exec } = require("child_process");
// const { MongoClient } = require("mongodb");
// const path = require("path");

// const app = express();
// const port = 3000;

// // Serve HTML page at /home
// app.get("/home", (req, res) => {
//     res.sendFile(path.join(__dirname, "public", "index.html"));
// });

// // MongoDB setup
// const uri = "mongodb://127.0.0.1:27017";
// const client = new MongoClient(uri);
// const dbName = "Contests";
// const collectionName = "codes";

// // Run Python scripts and fetch DB data
// app.get("/run-and-fetch", async (req, res) => {
//     // Run test.py first
//     exec("python test.py", { cwd: __dirname }, (err1) => {
//         if (err1) {
//             console.error("Error running test.py:", err1);
//             return res.status(500).send("Error running test.py");
//         }
//         console.log("test.py executed");

//         // Run rand.py next
//         exec("python rand.py", { cwd: __dirname }, async (err2) => {
//             if (err2) {
//                 console.error("Error running rand.py:", err2);
//                 return res.status(500).send("Error running rand.py");
//             }
//             console.log("rand.py executed");

//             // Fetch data from MongoDB
//             try {
//                 await client.connect();
//                 const db = client.db(dbName);
//                 const collection = db.collection(collectionName);
//                 const data = await collection.find({}).toArray();
//                 res.json(data);
//             } catch (dbErr) {
//                 console.error(dbErr);
//                 res.status(500).send("Database error");
//             }
//         });
//     });
// });

// app.listen(port, () => {
//     console.log(`Server running at http://localhost:${port}/home`);
// });



const express = require("express");
const bodyParser = require("body-parser");
const { exec } = require("child_process");
const { MongoClient } = require("mongodb");
const path = require("path");

const app = express();
app.use(bodyParser.json());
app.use(express.static(path.join(__dirname, "public")));

app.get("/", (req, res) => {
  res.sendFile(path.join(__dirname, "public", "index.html"));
});

// Helper to run Python scripts sequentially
const runPython = (command) => {
  return new Promise((resolve, reject) => {
    exec(command, (err, stdout, stderr) => {
      console.log("Running:", command);
      if (stdout) console.log("STDOUT:", stdout);
      if (stderr) console.log("STDERR:", stderr);
      if (err) return reject(stderr || "Python script failed");
      resolve(stdout);
    });
  });
};

app.post("/run", async (req, res) => {
  const { username, password, contest } = req.body;

  if (!username || !password || !contest) {
    return res.json({ error: "All fields are required!" });
  }

  try {
    // Run Python scripts sequentially
    await runPython(`python test.py "${username}" "${password}" "${contest}"`);
    await runPython(`python similar.py`);
    await runPython(`python rand.py`);

    // Fetch MongoDB data, exclude _id
    const client = await MongoClient.connect("mongodb://localhost:27017/");
    const db = client.db("Contests");
    const data = await db.collection("codes")
      .find({}, { projection: { _id: 0, teamname: 1, lang: 1, copiedfrom: 1, code: 1 } })
      .toArray();
    client.close();

    if (!data || data.length === 0) {
      return res.json({ error: "No data found in DB after scripts ran." });
    }

    res.json(data); // send DB data to frontend

  } catch (err) {
    console.error("Error:", err);
    res.json({ error: err.toString() });
  }
});

app.listen(3000, () => console.log("Server running on http://localhost:3000"));
