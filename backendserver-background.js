// backend/server.js
const express = require('express');
const mysql = require('mysql');
const cors = require('cors'); // Required for Cross-Origin Resource Sharing

const app = express();
const port = 3000; // The port your backend server will listen on

// Enable CORS for all origins (for development purposes)
// In a production environment, you should restrict this to your frontend's domain.
app.use(cors());

// Create a MySQL connection pool
// Using a pool is more efficient for managing multiple connections
const pool = mysql.createPool({
    connectionLimit: 10, // Max number of connections in the pool
    host: 'scdb-1.cbescsscomlo.us-east-2.rds.amazonaws.com',   // Your MySQL host (e.g., 'localhost' or an IP address)
    user: 'admin', // Your MySQL username
    password: 'jNaCvtxtcYMXLx0i1cBq', // Your MySQL password
    database: 'sckill-leaderboard'       // The name of your database
});

// Test database connection
pool.getConnection((err, connection) => {
    if (err) {
        console.error('Error connecting to the database:', err.stack);
        return;
    }
    console.log('Connected to MySQL database as id ' + connection.threadId);
    connection.release(); // Release the connection back to the pool
});

// API endpoint to get user data
app.get('/api/player_stats', (req, res) => {
    const query = 'SELECT id, handle, kills, deaths FROM player_stats'; // SQL query to fetch data

    pool.query(query, (error, results) => {
        if (error) {
            console.error('Error executing query:', error);
            return res.status(500).json({ error: 'Failed to fetch data' });
        }
        // Send the fetched data as JSON
        res.json(results);
    });
});

// Start the server
app.listen(port, () => {
    console.log(`Backend server listening at http://localhost:${port}`);
    console.log(`Access user data at http://localhost:${port}/api/users`);
});

/*
To run this backend:
1. Save the code as `server.js` in your `my-backend` directory.
2. Open your terminal in the `my-backend` directory.
3. Run: `node server.js`
4. Ensure your MySQL server is running and accessible with the provided credentials.
*/
