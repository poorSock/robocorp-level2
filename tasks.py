from robocorp.tasks import task
from robocorp import browser
from RPA.HTTP import HTTP
from RPA.Tables import Tables
from RPA.PDF import PDF
from RPA.FileSystem import FileSystem
from RPA.Archive import Archive

@task
def order_robots_from_RobotSpareBin():
    """
    Orders robots from RobotSpareBin Industries Inc.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates ZIP archive of the receipts and the images.
    """
    browser.configure(
        slowmo=50,
        )
    pending_orders = get_pending_orders_from_rsb()
    open_robot_order_website()
    for pending_order in pending_orders:
        order_robot(pending_order)
    create_order_zip_file()

def get_pending_orders_from_rsb():
    http = HTTP()
    http.download("https://robotsparebinindustries.com/orders.csv", overwrite=True)
    return Tables().read_table_from_csv("orders.csv", header=True, delimiters=",")

def open_robot_order_website():
    browser.goto("https://robotsparebinindustries.com/#/robot-order")
    close_annoying_modal()

def close_annoying_modal():
    """Closes the annoying modal that pops up every time we want to order a robot"""
    page = browser.page()
    page.click("text=Yep")

def order_not_successful():
    """Checks if the order was successful"""
    page = browser.page()
    receipt = page.get_by_text("Receipt")
    return not receipt.is_visible()

def order_robot(pending_order):
    """Orders a robot from the pending orders list"""
    page = browser.page()
    page.select_option("#head", pending_order["Head"])
    page.check("#id-body-" + pending_order["Body"])
    page.get_by_placeholder("Enter the part number for the legs").fill(pending_order["Legs"])
    page.fill("#address", pending_order["Address"])
    while (order_not_successful()):
        page.click("#order")
    save_order_summary(pending_order["Order number"])
    page.click("#order-another")
    close_annoying_modal()

def save_order_summary(order_number):
    """Saves the receipt and the picture of the ordered robot as a PDF"""
    pdf_path = save_receipt(order_number)
    screenshot_path = save_picture(order_number)
    embed_picture_in_pdf(pdf_path, screenshot_path)


def save_receipt(order_number):
    page = browser.page()
    page.screenshot()
    receipt_html = page.locator("#receipt").inner_html()
    pdf = PDF()
    path = f"output/receipts/robot_order_nr_{order_number}.pdf"
    pdf.html_to_pdf(receipt_html, path)
    return path

def save_picture(order_number):
    page = browser.page()
    path = f"output/previews/robot_order_nr_{order_number}.png"
    page.locator("#robot-preview-image").screenshot(path=path)
    return path

def embed_picture_in_pdf(pdf_path, screenshot_path):
    """Connects the order receipt with the picture of the ordered robot"""
    pdf = PDF()
    pdf.add_files_to_pdf(files=[screenshot_path], target_document=pdf_path, append=True)
    fileSystem = FileSystem()
    fileSystem.remove_file(screenshot_path)

    
def create_order_zip_file():
    """Creates an ZIP File with all ordered robot receipts"""
    archive = Archive()
    archive.archive_folder_with_zip("output/receipts", "output/robot_orders.zip")

