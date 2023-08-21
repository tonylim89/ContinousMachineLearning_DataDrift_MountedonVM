<?php
// Database configuration
$servername = "xxx";
$username = "xxx";
$password = "xxx";
$dbname = "xxx";

// Create connection
$conn = new mysqli($servername, $username, $password, $dbname);

// Check connection
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

set_error_handler(function($errno, $errstr, $errfile, $errline ) {
    throw new ErrorException($errstr, $errno, 0, $errfile, $errline);
});

$station_ids = ['S24', 'S43', 'S44', 'S50', 'S60', 'S104', 'S106', 'S107', 'S108', 'S109', 'S111', 'S115', 'S116', 'S117', 'S121'];

// If the missing data file doesn't exist, initialize it with an empty array
if (!file_exists('missing_data_frames.txt')) {
    file_put_contents('missing_data_frames.txt', serialize([]));
}

$missing_data_frames = unserialize(file_get_contents('missing_data_frames.txt'));

// Set the default timezone to Singapore
date_default_timezone_set('Asia/Singapore');

$current_time = new DateTime();
$current_time->setTime($current_time->format('H'), $current_time->format('i'), 0);

$api_time = clone $current_time;
$api_time->modify('-1 minute');

$api_time_str = $api_time->format('Y-m-d\TH:i:00');

try {
    $temp_response = file_get_contents("https://api.data.gov.sg/v1/environment/air-temperature?date_time=$api_time_str");
    $hum_response = file_get_contents("https://api.data.gov.sg/v1/environment/relative-humidity?date_time=$api_time_str");
} catch (Exception $e) {
    // If an error occurred, consider this frame as missing and try again in the next run
    foreach ($station_ids as $station_id) {
        $missing_data_frames[$api_time_str][] = $station_id;
    }
}

    $temp_data = json_decode($temp_response, true);
    $hum_data = json_decode($hum_response, true);

    $temp_values = [];
    foreach ($temp_data['items'][0]['readings'] as $reading) {
        $temp_values[$reading['station_id']] = $reading['value'];
    }

    $hum_values = [];
    foreach ($hum_data['items'][0]['readings'] as $reading) {
        $hum_values[$reading['station_id']] = $reading['value'];
    }

    foreach ($station_ids as $station_id) {
        if (!isset($temp_values[$station_id]) || !isset($hum_values[$station_id])) {
            $missing_data_frames[$api_time_str][] = $station_id;
        } else {
            $temperature = $temp_values[$station_id];
            $humidity = $hum_values[$station_id];

            $sql = "INSERT INTO temperature_data (station_id, temperature, humidity, timestamp) 
                    VALUES ('$station_id', $temperature, $humidity, '$api_time_str')
                    ON DUPLICATE KEY UPDATE temperature = $temperature, humidity = $humidity";

            if ($conn->query($sql) === FALSE) {
                echo "Error: " . $sql . "<br>" . $conn->error;
            }
        }
    }


foreach ($missing_data_frames as $frame_time_str => $missing_station_ids) {
    $frame_time = new DateTime($frame_time_str);
    if ($current_time->getTimestamp() - $frame_time->getTimestamp() > 20 * 60) {
        unset($missing_data_frames[$frame_time_str]);
    } else {
        try {
            $temp_response = file_get_contents("https://api.data.gov.sg/v1/environment/air-temperature?date_time=$frame_time_str");
            $hum_response = file_get_contents("https://api.data.gov.sg/v1/environment/relative-humidity?date_time=$frame_time_str");
        } catch (Exception $e) {
            //catch to continue
        }

        $temp_data = json_decode($temp_response, true);
        $hum_data = json_decode($hum_response, true);

        $temp_values = [];
        foreach ($temp_data['items'][0]['readings'] as $reading) {
            $temp_values[$reading['station_id']] = $reading['value'];
        }

        $hum_values = [];
        foreach ($hum_data['items'][0]['readings'] as $reading) {
            $hum_values[$reading['station_id']] = $reading['value'];
        }

        foreach ($missing_station_ids as $key => $station_id) {
            if (isset($temp_values[$station_id]) && isset($hum_values[$station_id])) {
                $temperature = $temp_values[$station_id];
                $humidity = $hum_values[$station_id];

                $sql = "INSERT INTO temperature_data (station_id, temperature, humidity, timestamp) 
                        VALUES ('$station_id', $temperature, $humidity, '$frame_time_str')
                        ON DUPLICATE KEY UPDATE temperature = $temperature, humidity = $humidity";

                if ($conn->query($sql) === FALSE) {
                    echo "Error: " . $sql . "<br>" . $conn->error;
                }

                unset($missing_data_frames[$frame_time_str][$key]);
            }
        }

        if (empty($missing_data_frames[$frame_time_str])) {
            unset($missing_data_frames[$frame_time_str]);
        }
    }
}

file_put_contents('missing_data_frames.txt', serialize($missing_data_frames));

$conn->close();
?>
