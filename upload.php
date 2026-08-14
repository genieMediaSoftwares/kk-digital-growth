<?php
/**
 * Hostinger Direct Image Upload Endpoint with Strict Verification & Diagnostics
 * Hostinger Location: /home/u394319514/public_html/upload.php
 * Target Directory: /home/u394319514/public_html/uploads/
 */

header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Origin: *");
header("Access-Control-Allow-Methods: GET, POST, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With");

function log_upload_debug($message, $data = null) {
    $logFile = __DIR__ . '/upload_debug.log';
    $timestamp = date('Y-m-d H:i:s');
    $logEntry = "[{$timestamp}] {$message}";
    if ($data !== null) {
        $logEntry .= " | Data: " . (is_string($data) ? $data : json_encode($data));
    }
    $logEntry .= "\n";
    @file_put_contents($logFile, $logEntry, FILE_APPEND);
}

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    echo json_encode(["success" => true, "message" => "CORS preflight OK"]);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    $targetDir = __DIR__ . "/uploads/";
    $isWritable = is_dir($targetDir) && is_writable($targetDir);
    log_upload_debug("GET Reachability Health Check executed", ["writable" => $isWritable]);
    http_response_code(200);
    echo json_encode([
        "status" => "active",
        "message" => "Hostinger upload API endpoint is reachable.",
        "server_time" => date('Y-m-d H:i:s'),
        "uploads_dir_writable" => $isWritable
    ]);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    log_upload_debug("ERROR: Disallowed HTTP Method", $_SERVER['REQUEST_METHOD']);
    http_response_code(405);
    echo json_encode([
        "success" => false,
        "message" => "Invalid request method '{$_SERVER['REQUEST_METHOD']}'. Only POST is allowed for uploads."
    ]);
    exit;
}

if (!isset($_FILES["image"]) || empty($_FILES["image"]["name"])) {
    log_upload_debug("ERROR: Missing $_FILES['image'] payload", $_FILES);
    http_response_code(400);
    echo json_encode([
        "success" => false,
        "message" => "No image file payload provided in multipart/form-data request under key 'image'."
    ]);
    exit;
}

$file = $_FILES["image"];
log_upload_debug("File Payload Received", ["name" => $file["name"], "size" => $file["size"], "tmp_name" => $file["tmp_name"], "error" => $file["error"]]);

if ($file["error"] !== UPLOAD_ERR_OK) {
    $uploadErrors = [
        UPLOAD_ERR_INI_SIZE   => "The uploaded file exceeds upload_max_filesize in php.ini.",
        UPLOAD_ERR_FORM_SIZE  => "The uploaded file exceeds MAX_FILE_SIZE specified in HTML form.",
        UPLOAD_ERR_PARTIAL    => "The uploaded file was only partially uploaded.",
        UPLOAD_ERR_NO_FILE    => "No file was uploaded.",
        UPLOAD_ERR_NO_TMP_DIR => "Missing a temporary folder on server.",
        UPLOAD_ERR_CANT_WRITE => "Failed to write file to disk.",
        UPLOAD_ERR_EXTENSION  => "A PHP extension stopped the file upload."
    ];
    $errMsg = $uploadErrors[$file["error"]] ?? ("PHP Upload Error Code: " . $file["error"]);
    log_upload_debug("ERROR: PHP Upload Status Code Failure", $errMsg);
    http_response_code(400);
    echo json_encode([
        "success" => false,
        "message" => $errMsg
    ]);
    exit;
}

$ext = strtolower(pathinfo($file["name"], PATHINFO_EXTENSION));
if (!$ext || $ext === 'jpg') {
    $ext = 'jpeg';
}

$allowedExtensions = ["jpg", "jpeg", "png", "gif", "webp"];
if (!in_array($ext, $allowedExtensions)) {
    log_upload_debug("ERROR: Invalid Extension", ["ext" => $ext]);
    http_response_code(400);
    echo json_encode([
        "success" => false,
        "message" => "Invalid file extension '.{$ext}'. Allowed formats: JPG, JPEG, PNG, GIF, WEBP."
    ]);
    exit;
}

$maxBytes = 5 * 1024 * 1024;
if ($file["size"] > $maxBytes) {
    log_upload_debug("ERROR: File too large", ["size" => $file["size"]]);
    http_response_code(400);
    echo json_encode([
        "success" => false,
        "message" => "Image is " . round($file["size"] / 1048576, 1) . " MB. Maximum allowed size is 5 MB."
    ]);
    exit;
}

$imageInfo = @getimagesize($file["tmp_name"]);
$allowedImageTypes = [IMAGETYPE_JPEG, IMAGETYPE_PNG, IMAGETYPE_GIF, IMAGETYPE_WEBP];
if ($imageInfo === false || !in_array($imageInfo[2], $allowedImageTypes)) {
    log_upload_debug("ERROR: Payload is not a real image", ["name" => $file["name"]]);
    http_response_code(400);
    echo json_encode([
        "success" => false,
        "message" => "The uploaded file is not a valid JPG, PNG, GIF or WEBP image."
    ]);
    exit;
}

$targetDir = __DIR__ . "/uploads/";
if (!is_dir($targetDir)) {
    log_upload_debug("Creating directory uploads/...");
    if (!@mkdir($targetDir, 0755, true)) {
        log_upload_debug("ERROR: Failed to mkdir uploads/", $targetDir);
        http_response_code(500);
        echo json_encode([
            "success" => false,
            "message" => "Hostinger Permission Error: Failed to create directory 'public_html/uploads/'."
        ]);
        exit;
    }
}

if (!is_writable($targetDir)) {
    log_upload_debug("ERROR: Directory uploads/ not writable", $targetDir);
    http_response_code(500);
    echo json_encode([
        "success" => false,
        "message" => "Hostinger Permission Error: Directory 'public_html/uploads/' is not writable."
    ]);
    exit;
}

$timestamp = time();
$millis = round(microtime(true) * 1000);
$randNum = mt_rand(100000000, 999999999);
$newName = "{$timestamp}_{$millis}-{$randNum}.{$ext}";

$destination = $targetDir . $newName;
$attempts = 0;
while (file_exists($destination) && $attempts < 10) {
    $randNum = mt_rand(100000000, 999999999);
    $newName = "{$timestamp}_{$millis}-{$randNum}.{$ext}";
    $destination = $targetDir . $newName;
    $attempts++;
}

log_upload_debug("Moving file", ["tmp" => $file["tmp_name"], "dest" => $destination]);
if (move_uploaded_file($file["tmp_name"], $destination)) {
    
    if (file_exists($destination) && filesize($destination) > 0) {
        // Derive the public host from the request instead of hard-coding it, so
        // the returned URL always matches the hostname that served this upload.
        $scheme = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off') ? 'https' : 'http';
        $host = $_SERVER['HTTP_HOST'] ?? ($_SERVER['SERVER_NAME'] ?? 'kkdigitalgrowth.com');
        $publicDomain = $scheme . "://" . $host;
        $publicUrl = $publicDomain . "/uploads/" . $newName;
        
        log_upload_debug("VERIFIED SUCCESS", ["url" => $publicUrl, "size" => filesize($destination)]);
        
        http_response_code(200);
        echo json_encode([
            "success" => true,
            "verified" => true,
            "url" => $publicUrl,
            "filename" => $newName,
            "size" => filesize($destination)
        ]);
        exit;
    } else {
        log_upload_debug("ERROR: Post-move file verification failed", $destination);
        http_response_code(500);
        echo json_encode([
            "success" => false,
            "message" => "Hostinger File Verification Error: Moved file could not be verified in public_html/uploads/."
        ]);
        exit;
    }

} else {
    log_upload_debug("ERROR: move_uploaded_file failed", ["tmp" => $file["tmp_name"], "dest" => $destination]);
    http_response_code(500);
    echo json_encode([
        "success" => false,
        "message" => "Hostinger Server Error: move_uploaded_file failed. Check folder permissions."
    ]);
    exit;
}
