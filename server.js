const express = require('express');
const multer = require('multer');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = 3499;

// 中间件设置
app.use(express.static(path.join(__dirname, 'public')));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// 确保projec/images目录存在
const uploadDir = path.join(__dirname, 'projec/images');
if (!fs.existsSync(uploadDir)) {
    fs.mkdirSync(uploadDir, { recursive: true });
    console.log(`已创建上传目录: ${uploadDir}`);
}

// 配置multer用于文件上传
const storage = multer.diskStorage({
    destination: function (req, file, cb) {
        cb(null, uploadDir);
    },
    filename: function (req, file, cb) {
        // 生成唯一文件名，避免冲突
        const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
        cb(null, file.fieldname + '-' + uniqueSuffix + path.extname(file.originalname));
    }
});

const upload = multer({ 
    storage: storage,
    limits: {
        fileSize: 10 * 1024 * 1024 // 10MB限制
    },
    fileFilter: function (req, file, cb) {
        // 只允许图片文件
        if (file.mimetype.startsWith('image/')) {
            cb(null, true);
        } else {
            cb(new Error('只允许上传图片文件'), false);
        }
    }
});

// 根路径路由 - 提供前端页面
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

// 上传接口
app.post('/upload', upload.array('images', 10), (req, res) => {
    try {
        if (!req.files || req.files.length === 0) {
            return res.status(400).json({
                success: false,
                message: '没有接收到文件'
            });
        }

        // 返回上传成功的文件信息
        const uploadedFiles = req.files.map(file => ({
            name: file.filename,
            originalName: file.originalname,
            size: file.size,
            path: file.path
        }));

        res.json({
            success: true,
            message: '文件上传成功',
            uploadedCount: uploadedFiles.length,
            uploadedFiles: uploadedFiles
        });
    } catch (error) {
        console.error('上传错误:', error);
        res.status(500).json({
            success: false,
            message: '服务器内部错误'
        });
    }
});

// 获取已上传图片列表
app.get('/images', (req, res) => {
    try {
        fs.readdir(uploadDir, (err, files) => {
            if (err) {
                return res.status(500).json({
                    success: false,
                    message: '无法读取图片目录'
                });
            }

            const imageFiles = files.filter(file => {
                const ext = path.extname(file).toLowerCase();
                return ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'].includes(ext);
            });

            const images = imageFiles.map(file => {
                const filePath = path.join(uploadDir, file);
                const stats = fs.statSync(filePath);
                
                return {
                    name: file,
                    size: stats.size,
                    url: `./projec/images/${file}`
                };
            });

            res.json({
                success: true,
                images: images
            });
        });
    } catch (error) {
        console.error('获取图片列表错误:', error);
        res.status(500).json({
            success: false,
            message: '服务器内部错误'
        });
    }
});

// 静态文件服务，用于访问上传的图片
app.use('projec/images', express.static(uploadDir));

// 错误处理中间件
app.use((error, req, res, next) => {
    if (error instanceof multer.MulterError) {
        if (error.code === 'LIMIT_FILE_SIZE') {
            return res.status(400).json({
                success: false,
                message: '文件大小超过限制'
            });
        }
    }
    
    res.status(500).json({
        success: false,
        message: error.message
    });
});

// 处理404错误
app.use((req, res) => {
    res.status(404).json({
        success: false,
        message: '请求的路径不存在'
    });
});

app.listen(PORT, () => {
    console.log(`服务器运行在 http://localhost:${PORT}`);
    console.log(`图片上传目录: ${uploadDir}`);
});