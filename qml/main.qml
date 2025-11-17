import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

ApplicationWindow {
    id: mainWindow
    visible: true
    width: 900
    height: 700
    minimumWidth: 800
    minimumHeight: 600
    title: "数据库备份同步工具"

    // 设置 Windows 11 风格
    color: "#F3F3F3"

    // 主布局
    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // 标题栏
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 60
            color: "#FFFFFF"
            
            RowLayout {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 15

                Image {
                    source: "file:///" + Qt.resolvedUrl("../resource/icon.png")
                    Layout.preferredWidth: 32
                    Layout.preferredHeight: 32
                    fillMode: Image.PreserveAspectFit
                    visible: status === Image.Ready
                }

                Label {
                    text: "数据库备份同步工具"
                    font.pixelSize: 20
                    font.bold: true
                    color: "#202020"
                }

                Item { Layout.fillWidth: true }

                Label {
                    text: "v1.0.0"
                    font.pixelSize: 12
                    color: "#666666"
                }
            }

            Rectangle {
                anchors.bottom: parent.bottom
                width: parent.width
                height: 1
                color: "#E0E0E0"
            }
        }

        // 主内容区域
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            RowLayout {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 20

                // 左侧配置面板
                Rectangle {
                    Layout.preferredWidth: 350
                    Layout.fillHeight: true
                    color: "#FFFFFF"
                    radius: 8
                    border.color: "#E0E0E0"
                    border.width: 1

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 20
                        spacing: 15

                        Label {
                            text: "数据库配置"
                            font.pixelSize: 16
                            font.bold: true
                            color: "#202020"
                        }

                        // 同步类型选择
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            Label {
                                text: "同步类型"
                                font.pixelSize: 13
                                color: "#666666"
                            }

                            ComboBox {
                                id: syncTypeCombo
                                Layout.fillWidth: true
                                model: ["远程到本地", "本地到远程", "导出SQL", "执行SQL"]
                                font.pixelSize: 13
                            }
                        }

                        // 主机地址
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            Label {
                                text: "主机地址"
                                font.pixelSize: 13
                                color: "#666666"
                            }

                            TextField {
                                id: hostInput
                                Layout.fillWidth: true
                                placeholderText: "localhost"
                                text: "localhost"
                                font.pixelSize: 13
                            }
                        }

                        // 端口
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            Label {
                                text: "端口"
                                font.pixelSize: 13
                                color: "#666666"
                            }

                            TextField {
                                id: portInput
                                Layout.fillWidth: true
                                placeholderText: "3306"
                                text: "3306"
                                font.pixelSize: 13
                                validator: IntValidator { bottom: 1; top: 65535 }
                            }
                        }

                        // 用户名
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            Label {
                                text: "用户名"
                                font.pixelSize: 13
                                color: "#666666"
                            }

                            TextField {
                                id: userInput
                                Layout.fillWidth: true
                                placeholderText: "root"
                                text: "root"
                                font.pixelSize: 13
                            }
                        }

                        // 密码
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            Label {
                                text: "密码"
                                font.pixelSize: 13
                                color: "#666666"
                            }

                            TextField {
                                id: passwordInput
                                Layout.fillWidth: true
                                placeholderText: "请输入密码"
                                echoMode: TextInput.Password
                                font.pixelSize: 13
                            }
                        }

                        // 数据库名
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            Label {
                                text: "数据库名"
                                font.pixelSize: 13
                                color: "#666666"
                            }

                            TextField {
                                id: databaseInput
                                Layout.fillWidth: true
                                placeholderText: "请输入数据库名"
                                font.pixelSize: 13
                            }
                        }

                        // SQL 文件选择（仅执行SQL时显示）
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            visible: syncTypeCombo.currentText === "执行SQL"

                            Label {
                                text: "SQL 文件"
                                font.pixelSize: 13
                                color: "#666666"
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 8

                                TextField {
                                    id: sqlFileInput
                                    Layout.fillWidth: true
                                    placeholderText: "选择 SQL 文件"
                                    font.pixelSize: 13
                                    readOnly: true
                                }

                                Button {
                                    text: "浏览"
                                    onClicked: backend.selectSqlFile()
                                }
                            }
                        }

                        Item { Layout.fillHeight: true }

                        // 开始按钮
                        Button {
                            id: startButton
                            Layout.fillWidth: true
                            Layout.preferredHeight: 45
                            text: "开始同步"
                            font.pixelSize: 14
                            font.bold: true
                            
                            background: Rectangle {
                                color: startButton.pressed ? "#0078D4" : (startButton.hovered ? "#106EBE" : "#0067C0")
                                radius: 6
                            }
                            
                            contentItem: Text {
                                text: startButton.text
                                font: startButton.font
                                color: "#FFFFFF"
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }

                            onClicked: {
                                backend.startSync(
                                    syncTypeCombo.currentText,
                                    hostInput.text,
                                    parseInt(portInput.text),
                                    userInput.text,
                                    passwordInput.text,
                                    databaseInput.text,
                                    sqlFileInput.text
                                )
                            }
                        }
                    }
                }

                // 右侧日志面板
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: "#FFFFFF"
                    radius: 8
                    border.color: "#E0E0E0"
                    border.width: 1

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 20
                        spacing: 15

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 10

                            Label {
                                text: "同步日志"
                                font.pixelSize: 16
                                font.bold: true
                                color: "#202020"
                            }

                            Item { Layout.fillWidth: true }

                            Button {
                                text: "清空日志"
                                font.pixelSize: 12
                                onClicked: logOutput.text = ""
                                
                                background: Rectangle {
                                    color: parent.pressed ? "#E0E0E0" : (parent.hovered ? "#F0F0F0" : "#F8F8F8")
                                    radius: 4
                                    border.color: "#D0D0D0"
                                    border.width: 1
                                }
                            }
                        }

                        ScrollView {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            clip: true

                            TextArea {
                                id: logOutput
                                readOnly: true
                                wrapMode: TextEdit.Wrap
                                font.family: "Consolas"
                                font.pixelSize: 12
                                color: "#303030"
                                selectByMouse: true
                                
                                background: Rectangle {
                                    color: "#FAFAFA"
                                    border.color: "#E0E0E0"
                                    border.width: 1
                                    radius: 4
                                }
                            }
                        }

                        // 进度指示器
                        ProgressBar {
                            id: progressBar
                            Layout.fillWidth: true
                            visible: false
                            indeterminate: true
                        }
                    }
                }
            }
        }

        // 状态栏
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 35
            color: "#FFFFFF"
            
            Rectangle {
                anchors.top: parent.top
                width: parent.width
                height: 1
                color: "#E0E0E0"
            }

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 20
                anchors.rightMargin: 20
                spacing: 10

                Label {
                    id: statusLabel
                    text: "就绪"
                    font.pixelSize: 12
                    color: "#666666"
                }

                Item { Layout.fillWidth: true }

                Label {
                    text: "© 2025 Database Backup Tool"
                    font.pixelSize: 11
                    color: "#999999"
                }
            }
        }
    }

    // 连接后端信号
    Connections {
        target: backend
        
        function onLogUpdated(message) {
            logOutput.append(message)
        }
        
        function onStatusChanged(status) {
            statusLabel.text = status
        }
        
        function onSyncStarted() {
            startButton.enabled = false
            progressBar.visible = true
            statusLabel.text = "同步中..."
        }
        
        function onSyncFinished(success, message) {
            startButton.enabled = true
            progressBar.visible = false
            statusLabel.text = success ? "同步完成" : "同步失败"
            logOutput.append("\n" + (success ? "✓ " : "✗ ") + message + "\n")
        }
        
        function onSqlFileSelected(filePath) {
            sqlFileInput.text = filePath
        }
    }
}
