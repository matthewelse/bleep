use std::{collections::BTreeSet, sync::Arc};

use btleplug::{
    api::{
        Central, Characteristic, Descriptor, Manager as _, Peripheral as _, PeripheralProperties,
        ScanFilter, Service, ValueNotification, WriteType,
    },
    platform::{Adapter, Manager, Peripheral, PeripheralId},
};
use pyo3::{exceptions::PyValueError, prelude::*};
use tokio_stream::StreamExt;

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord)]
#[pyclass]
struct BleDescriptor(Descriptor);

#[pymethods]
impl BleDescriptor {
    fn uuid(&self) -> String {
        self.0.uuid.to_string()
    }

    fn __repr__(&self) -> String {
        format!("{self:?}")
    }
}

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord)]
#[pyclass]
struct BleCharacteristic(Characteristic);

#[pymethods]
impl BleCharacteristic {
    fn descriptors(&self) -> BTreeSet<BleDescriptor> {
        self.0
            .descriptors
            .iter()
            .map(|x| BleDescriptor(x.clone()))
            .collect()
    }

    fn uuid(&self) -> String {
        self.0.uuid.to_string()
    }

    fn __repr__(&self) -> String {
        format!("{self:?}")
    }
}

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord)]
#[pyclass]
struct BleService(Service);

#[pymethods]
impl BleService {
    fn uuid(&self) -> String {
        self.0.uuid.to_string()
    }

    fn characteristics(&self) -> BTreeSet<BleCharacteristic> {
        self.0
            .characteristics
            .iter()
            .map(|x| BleCharacteristic(x.clone()))
            .collect()
    }

    fn __repr__(&self) -> String {
        format!("{self:?}")
    }
}

#[derive(Debug)]
#[pyclass]
struct BlePeripheralId(PeripheralId);

#[pymethods]
impl BlePeripheralId {
    fn __repr__(&self) -> String {
        format!("{self:?}")
    }
}

#[derive(Debug)]
#[pyclass]
struct BlePeripheralProperties(Arc<PeripheralProperties>);

#[pymethods]
impl BlePeripheralProperties {
    fn local_name(&self) -> Option<String> {
        self.0.local_name.clone()
    }

    fn services(&self) -> Vec<String> {
        self.0.services.iter().map(|x| x.to_string()).collect()
    }

    fn __repr__(&self) -> String {
        format!("{self:?}")
    }
}

#[derive(Debug)]
#[pyclass]
struct BleValueNotification(ValueNotification);

#[derive(Debug)]
#[pyclass]
struct BlePeripheral(Arc<Peripheral>);

#[pymethods]
impl BlePeripheral {
    fn id(&self) -> BlePeripheralId {
        BlePeripheralId(self.0.id())
    }

    fn properties<'a>(&self, py: Python<'a>) -> PyResult<&'a PyAny> {
        let peripheral = self.0.clone();
        pyo3_asyncio::tokio::future_into_py(py, async move {
            let properties = peripheral
                .properties()
                .await
                .map_err(|x| PyValueError::new_err(x.to_string()))?;

            Ok(properties.map(|x| BlePeripheralProperties(Arc::new(x))))
        })
    }

    fn services<'a>(&self, py: Python<'a>) -> PyResult<&'a PyAny> {
        let peripheral = self.0.clone();
        pyo3_asyncio::tokio::future_into_py(py, async move {
            peripheral
                .discover_services()
                .await
                .map_err(|x| PyValueError::new_err(x.to_string()))?;
            let services = peripheral.services();

            Ok(services
                .into_iter()
                .map(BleService)
                .collect::<BTreeSet<_>>())
        })
    }

    fn connect<'a>(&self, py: Python<'a>) -> PyResult<&'a PyAny> {
        let peripheral = self.0.clone();
        pyo3_asyncio::tokio::future_into_py(py, async move {
            peripheral
                .connect()
                .await
                .map_err(|x| PyValueError::new_err(x.to_string()))?;

            Ok(())
        })
    }

    fn disconnect<'a>(&self, py: Python<'a>) -> PyResult<&'a PyAny> {
        let peripheral = self.0.clone();
        pyo3_asyncio::tokio::future_into_py(py, async move {
            peripheral
                .disconnect()
                .await
                .map_err(|x| PyValueError::new_err(x.to_string()))?;

            Ok(())
        })
    }

    fn address(&self) -> String {
        self.0.address().to_string()
    }

    fn write<'a>(
        &self,
        py: Python<'a>,
        characteristic: BleCharacteristic,
        data: Vec<u8>,
        with_response: bool,
    ) -> PyResult<&'a PyAny> {
        let peripheral = self.0.clone();
        let characteristic = characteristic.0;
        pyo3_asyncio::tokio::future_into_py(py, async move {
            peripheral
                .write(
                    &characteristic,
                    &data,
                    if with_response {
                        WriteType::WithResponse
                    } else {
                        WriteType::WithoutResponse
                    },
                )
                .await
                .map_err(|x| PyValueError::new_err(x.to_string()))?;

            Ok(())
        })
    }

    fn read<'a>(&self, py: Python<'a>, characteristic: BleCharacteristic) -> PyResult<&'a PyAny> {
        let peripheral = self.0.clone();
        let characteristic = characteristic.0;
        pyo3_asyncio::tokio::future_into_py(py, async move {
            peripheral
                .read(&characteristic)
                .await
                .map_err(|x| PyValueError::new_err(x.to_string()))
        })
    }

    fn register_notification_callback<'a>(
        &self,
        py: Python<'a>,
        // TODO: check the type of `Callback` before doing all of this async stuff.
        callback: PyObject,
    ) -> PyResult<&'a PyAny> {
        let peripheral = self.0.clone();
        pyo3_asyncio::tokio::future_into_py(py, async move {
            let mut stream = peripheral
                .notifications()
                .await
                .map_err(|x| PyValueError::new_err(x.to_string()))?;

            tokio::spawn(async move {
                while let Some(item) = stream.next().await {
                    Python::with_gil(|py| {
                        // TODO: handle exceptions here better.
                        let _: PyResult<PyObject> =
                            callback.call(py, (item.uuid.to_string(), item.value), None);
                    })
                }
            });

            Ok(())
        })
    }

    fn __repr__(&self) -> String {
        format!("{self:?}")
    }
}

#[derive(Debug)]
#[pyclass]
struct BleAdapter(Arc<Adapter>);

#[pymethods]
impl BleAdapter {
    fn adapter_info<'a>(&self, py: Python<'a>) -> PyResult<&'a PyAny> {
        let adapter = self.0.clone();
        pyo3_asyncio::tokio::future_into_py(py, async move {
            adapter
                .adapter_info()
                .await
                .map_err(|x| PyValueError::new_err(x.to_string()))
        })
    }

    fn start_scan<'a>(&self, py: Python<'a>) -> PyResult<&'a PyAny> {
        let adapter = self.0.clone();

        pyo3_asyncio::tokio::future_into_py(py, async move {
            adapter
                .start_scan(ScanFilter::default())
                .await
                .map_err(|x| PyValueError::new_err(x.to_string()))?;

            Ok(())
        })
    }

    fn peripherals<'a>(&self, py: Python<'a>) -> PyResult<&'a PyAny> {
        let adapter = self.0.clone();

        pyo3_asyncio::tokio::future_into_py(py, async move {
            let peripherals = adapter
                .peripherals()
                .await
                .map_err(|x| PyValueError::new_err(x.to_string()))?
                .into_iter()
                .map(|x| BlePeripheral(Arc::new(x)))
                .collect::<Vec<_>>();

            Ok(peripherals)
        })
    }

    fn __repr__(&self) -> String {
        format!("{self:?}")
    }
}

#[derive(Debug)]
#[pyclass]
struct BleManager(Arc<Manager>);

#[pymethods]
impl BleManager {
    #[allow(clippy::new_ret_no_self)]
    #[staticmethod]
    fn new(py: Python<'_>) -> PyResult<&PyAny> {
        pyo3_asyncio::tokio::future_into_py(py, async {
            Ok(BleManager(Arc::new(
                Manager::new()
                    .await
                    .map_err(|x| PyValueError::new_err(x.to_string()))?,
            )))
        })
    }
    fn adapters<'a>(&self, py: Python<'a>) -> PyResult<&'a PyAny> {
        let manager = self.0.clone();
        pyo3_asyncio::tokio::future_into_py(py, async move {
            let adapters = manager
                .adapters()
                .await
                .map_err(|x| PyValueError::new_err(x.to_string()))?
                .into_iter()
                .map(|x| BleAdapter(Arc::new(x)))
                .collect::<Vec<_>>();

            Ok(adapters)
        })
    }

    fn __repr__(&self) -> String {
        format!("{self:?}")
    }
}

#[pymodule]
fn bleep(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<BleManager>()?;
    m.add_class::<BleAdapter>()?;
    m.add_class::<BlePeripheral>()?;
    m.add_class::<BlePeripheralId>()?;
    m.add_class::<BlePeripheralProperties>()?;
    m.add_class::<BleService>()?;
    m.add_class::<BleCharacteristic>()?;
    m.add_class::<BleDescriptor>()?;
    m.add_class::<BleValueNotification>()?;
    Ok(())
}
