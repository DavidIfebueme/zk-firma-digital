#!python

# IMport the required libraries
import sys
import os
import json

from os import listdir
from os.path import isfile, join

# We will use the PyQt6 to provide a grafical interface for the user
# TODO: test that it works on Windows
from PyQt6.QtWidgets import ( QApplication,
                              QMainWindow,
                              QWidget,
                              QVBoxLayout,
                              QLineEdit,
                              QPushButton,
                              QMessageBox,
                              QTabWidget,
                              QLabel,
                              QFileDialog )

# Import our own libraries
from certificate import Certificate
from verification import Verification
from signature import Signature
from circom import Circom

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.build_path="../build/"
        self.credentials_path="../credentials/"
        self.certificate_path = self.build_path+"certificado.cert"
        self.file_to_sign = ""

        # Create a QLabel
        self.file_label = QLabel()
        # HTML link to the local file
        current_directory = os.getcwd()
        file_path = current_directory+"/"+self.credentials_path+"credential.json"
        self.file_label.setText(f'<a href="{file_path}">Haga click aquí para ver el archivo de credencial generado</a>')

        # Allow the QLabel to open external links
        self.file_label.setOpenExternalLinks(True)

        self.setWindowTitle("Zero Knowledge - Firma Digital")
        self.setGeometry(600, 400, 600, 400)

        # Create a QTabWidget
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Add tabs
        self.verification_tab = self.create_verification_tab()
        self.signing_tab = self.create_signing_tab()
        self.tabs.addTab(self.verification_tab, "Creación de credencial de prueba de conocimiento zero")

    def create_verification_tab(self):
        # Create the first tab's content
        verification_tab = QWidget(self)

        # Create a vertical layout
        self.verification_layout = QVBoxLayout()

        # Create the password field
        self.password_field = QLineEdit()
        self.password_field.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_field.setPlaceholderText("Introduzca el PIN de su tarjeta")
        self.verification_layout.addWidget(self.password_field)

        # Create the "Obtener certificados Firma Digital" button
        self.generate_credential_button = QPushButton("Generar credencial JSON")
        self.generate_credential_button.clicked.connect(self.on_submit_generate_credential)
        self.generate_credential_button.setStyleSheet("background-color : green")
        self.verification_layout.addWidget(self.generate_credential_button)

        # Set the layout for the central widget
        verification_tab.setLayout(self.verification_layout)
        return verification_tab

    def create_signing_tab(self):
        # Create the signature tab's content
        self.signature_tab = QWidget()
        self.signature_layout = QVBoxLayout()
        self.signature_layout.addWidget(QLabel("Firmar archivo JSON"))

        # Create the password field
        self.password_field_sign = QLineEdit()
        self.password_field_sign.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_field_sign.setPlaceholderText("Introduzca el PIN de su tarjeta")
        self.signature_layout.addWidget(self.password_field_sign)

        # Create a button to open the file dialog
        button_browser = QPushButton("Escoger archivo a firmar")
        button_browser.clicked.connect(self.browse_files)
        self.signature_layout.addWidget(button_browser)

        # Label to display the selected file
        self.browser_label = QLabel("Selected file: None")
        self.signature_layout.addWidget(self.browser_label)
        self.signature_tab.setLayout(self.signature_layout)

        # Create a button to sign the file
        button_sign = QPushButton("Firmar archivo")
        button_sign.clicked.connect(self.sign_files)
        self.signature_layout.addWidget(button_sign)

        return self.signature_tab

    def on_submit_generate_credential(self):
        self.generate_credential_button.setEnabled(False)
        self.generate_credential_button.setStyleSheet("background-color : gray")
        # Get the certificates from the card
        password = self.password_field.text()
        certificate = Certificate(password)
        (valid, info) = certificate.get_certificates()
        QMessageBox.information(self, "Certificados", f"{info}")
        if not valid:
            self.generate_credential_button.setEnabled(True)
            self.generate_credential_button.setStyleSheet("background-color : green")
            return
        # If the certificates were stored in disk then provide the option
        # to verify them
        if not os.path.exists(self.certificate_path):
            QMessageBox.information(self, "Certificado", "No se pudo obtener el certificado")
            self.generate_credential_button.setEnabled(True)
            self.generate_credential_button.setStyleSheet("background-color : green")
            return
        # Verify the stored certificates using the Goverment chain of trust
        password = self.password_field.text()
        verification = Verification(password)

        (valid, info) = verification.verify_certificate(self.certificate_path)
        if not valid:
            QMessageBox.information(self, "Validación", f"{info}\n\n Firma de certificado inválida!!!")
        else:
            QMessageBox.information(self, "Validación", f"{info}\n\n Firma de certificado válida!!!")
            circom = Circom()
            circom.generate_witness()
            circom.prove()
            circom.verify()

            # Create credential
            public_input_data = None
            proof_data = None

            with open(self.build_path+"public.json", 'r') as json_file:
                public_input_data = json.load(json_file)

            with open(self.build_path+"proof.json", 'r') as json_file:
                proof_data = json.load(json_file)

            # Structure json credential data
            credential_json_data = {
                "public": public_input_data,
                "proof": proof_data
            }

            # Create credential and store it in a file for the user to utilize
            with open(self.credentials_path+"credential.json", 'w', encoding='utf-8') as json_file:
                json.dump(credential_json_data, json_file, ensure_ascii=False, indent=4)

            self.verification_layout.addWidget(self.file_label)

            QMessageBox.information(self, "Creación de credencial válida", "Encontrar credenciales en el directorio credentials.")
        self.generate_credential_button.setEnabled(True)
        self.generate_credential_button.setStyleSheet("background-color : green")


    def browse_files(self):
        # Open a file dialog and select a file
        file_name, _ = QFileDialog.getOpenFileName(self,
                                                   "Open File",
                                                   "",
                                                   "JSON Files (*.json)")

        if file_name:
            self.browser_label.setText(f"Selected file: {file_name}")
            self.file_to_sign = file_name
        else:
            self.browser_label.setText("No file selected")

    # This code is not being used at the moment
    # Do we really need it?
    def sign_files(self):
        # Sign selected file
        password = self.password_field_sign.text()
        if self.file_to_sign:
            signature = Signature(password)
            signature.load_library()
            file_name = os.path.basename(self.file_to_sign)
            file_only_path = os.path.dirname(self.file_to_sign)
            signed_name = file_only_path+"/"+"signed-"+file_name
            info = signature.sign_file(self.file_to_sign)
            QMessageBox.information(self, "Firma de archivo JSON",
                                    f"{info}\n\nArchivo JSON firmado:\n\n {signed_name}")
            self.browser_label.setText(f"Archivo JSON firmado: {signed_name}")
        else:
            self.browser_label.setText("No file selected")

# Main entry point for our app
if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())