"""Interactive-free deterministic demo for Work Area 3."""
import argparse,json
from decimal import Decimal
from .ussd import Account,MobileMoneySimulator

def main():
    ap=argparse.ArgumentParser(description="SentiNet fictional USSD/mobile-money demo")
    ap.add_argument("--scenario",choices=["legitimate","failed-auth","transfer"],default="legitimate")
    args=ap.parse_args()
    app=MobileMoneySimulator(Account("USR-003","+251-900-000-003","1234",Decimal("500.00"),"ACC-003"))
    if args.scenario=="failed-auth":
        for _ in range(3): app.authenticate("0000")
    else:
        app.authenticate("1234")
        if args.scenario=="transfer": app.transfer("75.00")
        else: app.balance()
    print(json.dumps({"scenario":args.scenario,"account":app.snapshot(),
                      "events":[e.to_dict() for e in app.events]},indent=2))
if __name__=="__main__": main()
